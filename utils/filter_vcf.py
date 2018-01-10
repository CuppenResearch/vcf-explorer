"""Utility functions to filter vcf files."""
import sys

import vcf as py_vcf
import re

from . import db
from . import query


def filter_sv_vcf(vcf_file, flank=10, filter_name='DB', filter_query=False, filter_ori=False):
    """
    Parse vcf files and filter on database.

    Args:
        vcf_file (str): Path to vcf file
    """
    # Open vcf file
    try:
        vcf = py_vcf.Reader(open(vcf_file, 'r'))
    except IOError:
        sys.exit("Can't open vcf file: {0}".format(vcf_file))
    else:
        # setup filter
        db_filter = py_vcf.parser._Filter(filter_name, 'Similar variant found in database with {0}bp flank'.format(flank))
        vcf.filters[db_filter[0]] = db_filter
        notpresent_filter = py_vcf.parser._Filter("NotPresent", 'Similar variant is not found in the given sample(s)')
        vcf.filters[notpresent_filter[0]] = notpresent_filter
        
        vcf.infos['DB_Count'] = py_vcf.parser._Info('DB_Count', 1, 'Int', 'Variant count in database', 'vcf_explorer', '0.1')
        vcf.infos['DB_Frequency'] = py_vcf.parser._Info('DB_Frequency', 1, 'Float', 'Variant frequency in database', 'vcf_explorer', '0.1')
        if filter_query:
		query_filter = py_vcf.parser._Filter("DBQUERY", filter_query)
		sample_match_query = re.match(r"^SAMPLE(=|\!=|\?=)\[?(\S+)\]?", filter_query)
		if sample_match_query:
			my_sample_query = query.create_sample_query( filter_query )
	
        # output
        vcf_writer = py_vcf.Writer(sys.stdout, vcf)

        # Count number of samples in db for frequency
        query_aggregate = [
            {'$unwind': '$samples'},
            {'$group': {'_id': None, 'uniqueSamples': {'$addToSet': '$samples'}}},
            {'$count': 'samples_in_db'}
        ]
		
        #sampels_in_db = len(db.vcfs.distinct('samples', my_sample_query.replace('this.samples','this')))
        sampels_in_db = len(db.vcfs.distinct('samples'))
        
	for record in vcf:
		pos, ref, alt = get_minimal_representation(record.POS, str(record.REF), str(record.ALT))
		if ( isinstance(record.ALT[0], py_vcf.model._Breakend) ) :
			breakpoint = record.ALT[0]
			chr2 = breakpoint.chr
			end = breakpoint.pos
			alt = breakpoint.connectingSequence
			orientation = breakpoint.orientation
                        remoteOrientation = breakpoint.remoteOrientation
		else:
			if 'CHR2' in record.INFO:
				chr2 = record.INFO['CHR2']
			else:
				chr2 = record.CHROM
			if 'END' in record.INFO:
				end = record.INFO['END']
			else:
				end = False
		if record.CHROM == chr2:
			svlen = end-pos
		else:
			svlen = False
		if 'SVTYPE' in record.INFO:
			svtype = record.INFO['SVTYPE']
		else:
			svtype = False
		if svtype == 'DEL':
			orientation = False
			remoteOrientation = True
		elif svtype == 'INS':
			orientation = False
			remoteOrientation = True
		elif svtype == 'DUP':
			orientation = True
			remoteOrientation = False
		elif svtype != 'BND':
			orientation = 'UNKNOWN'
			remoteOrientation = 'UNKNOWN'
		if 'CIPOS' in record.INFO:
			pos1, pos2 = pos+record.INFO['CIPOS'][0], pos+record.INFO['CIPOS'][1]
		else:
			pos1, pos2 = pos, pos
                if 'CIEND' in record.INFO:
			end1, end2 = end+record.INFO['CIEND'][0], end+record.INFO['CIEND'][1]
		else:
			end1, end2 = end, end
		
		pos1, pos2 = pos1-flank, pos2+flank
		end1, end2 = end1-flank, end2+flank
		
		query_aggregate = [
                    {'$match': {
                        'chr': record.CHROM,
                        'chr2': chr2,
                        'samples': { '$elemMatch': { 'info.POS': { '$elemMatch': { '$gte': pos1, '$lte': pos2} }, 'info.END': { '$elemMatch': { '$gte': end1, '$lte': end2} } } },
			'$or': [
                            {'samples.sample': {'$nin': vcf.samples}},
                            {'samples.1': {'$exists': 'true'}}
                        ]
                    }},
                    {'$unwind': '$samples'},
                    {'$count': 'samples_with_variant'}
                ]

		# Add orientation filter
		if filter_ori:
			query_aggregate[0]['$match']['orientation'] = orientation
			query_aggregate[0]['$match']['remoteOrientation'] = remoteOrientation
		
		if filter_query:
			# If query is sample must
			if '$and' in my_sample_query and '$or' in my_sample_query:
				query_aggregate2 = list(query_aggregate)
				query_aggregate2[0]['$match'] = { '$and': [ query_aggregate2[0]['$match'], { '$and': my_sample_query['$and'] } ] }
				variant_aggregate2 = list(db.variants.aggregate(query_aggregate2))
				if not variant_aggregate2:
					record.add_filter(notpresent_filter[0])
				
				query_aggregate[0]['$match'] = { '$and': [ query_aggregate[0]['$match'], { '$or': my_sample_query['$or'] } ] }			
				
			else:
				query_aggregate[0]['$match'] = { '$and': [ query_aggregate[0]['$match'], my_sample_query ] }
				
		variant_aggregate = list(db.variants.aggregate(query_aggregate))
                
		db_count = 0
                db_frequency = 0.0
                if variant_aggregate:
                    record.add_filter(db_filter[0])
                    db_count = variant_aggregate[0]['samples_with_variant']
                    db_frequency = float(variant_aggregate[0]['samples_with_variant']) / sampels_in_db

                record.add_info('DB_Count', db_count)
                record.add_info('DB_Frequency', db_frequency)
                vcf_writer.write_record(record)

def get_minimal_representation(pos, ref, alt):
    """
    ExAC - MIT License (MIT)
    Copyright (c) 2014, Konrad Karczewski, Daniel MacArthur, Brett Thomas, Ben Weisburd

    Get the minimal representation of a variant, based on the ref + alt alleles in a VCF
    This is used to make sure that multiallelic variants in different datasets,
    with different combinations of alternate alleles, can always be matched directly.
    Args:
        pos (int): genomic position in a chromosome (1-based)
        ref (str): ref allele string
        alt (str): alt allele string
    Returns:
        tuple: (pos, ref, alt) of remapped coordinate
    """
    pos = int(pos)
    # If it's a simple SNV, don't remap anything
    if len(ref) == 1 and len(alt) == 1:
        return pos, ref, alt
    else:
        # strip off identical suffixes
        while(alt[-1] == ref[-1] and min(len(alt),len(ref)) > 1):
            alt = alt[:-1]
            ref = ref[:-1]
        # strip off identical prefixes and increment position
        while(alt[0] == ref[0] and min(len(alt),len(ref)) > 1):
            alt = alt[1:]
            ref = ref[1:]
            pos += 1
        return pos, ref, alt