

import pymongo

from . import connection, db

def create_indexes():
    """
    Create mongodb indexes.

    """

    # VCF collection indexes
    db.vcfs.drop_indexes()
    db.vcfs.create_index("name")
    db.vcfs.create_index("samples")
    db.vcfs.create_index( [ ("filename", pymongo.ASCENDING), ("fileformat", pymongo.ASCENDING), ("filedate", pymongo.ASCENDING) ], sparse=True )
    db.vcfs.create_index("run")

    # Variant collection indexes
    db.variants.drop_indexes()
    db.variants.create_index("samples.id")
    db.variants.create_index("samples.run")
    db.variants.create_index([("samples.id", pymongo.ASCENDING),("samples.filter", pymongo.ASCENDING)], sparse=True)
    db.variants.create_index( [ ("chr", pymongo.ASCENDING), ("pos", pymongo.ASCENDING), ("variant_info.chr2", pymongo.ASCENDING), ("variant_info.end", pymongo.ASCENDING), ("variant_info.svtype",         pymongo.ASCENDING),("variant_info.ct", pymongo.ASCENDING) ], sparse=True )

def resetdb():
    """
    Drop database and recreate indexes.
    """
    connection.drop_database('vcf_explorer')
    create_indexes()