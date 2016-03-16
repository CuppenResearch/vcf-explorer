import {Component} from 'angular2/core';
import {RouteParams} from 'angular2/router';

import {AgGridNg2} from 'ag-grid-ng2/main';
import {GridOptions} from 'ag-grid/main';

import {SampleService} from '../services/sample.service';

@Component({
  selector: 'sample',
  templateUrl:'/static/app/sample/components/sample.component.html',
  directives: [AgGridNg2],
  providers: [SampleService]
})
//export class SamplesComponent implements OnInit {
export class SampleComponent {
  private gridOptions: GridOptions;
  private sample: any[];
  private sampleVariants: any[];
  private columnDefs: any[];

  constructor(
    private _sampleService: SampleService,
    private _routeParams: RouteParams)
  {
    let sampleName = this._routeParams.get('name');
    this.gridOptions = <GridOptions>{};
    this.getSample(sampleName);
    this.getSampleVariants(sampleName);
    this.createColumnDefs();
  }

  private getSample(sampleName: string) {
    this._sampleService.getSample(sampleName).subscribe(
      sample => this.sample = sample
    );
  }

  private getSampleVariants(sampleName: string) {
    this._sampleService.getSampleVariants(sampleName).subscribe(
      sampleVariants => this.sampleVariants = sampleVariants
    );
  }

  private createColumnDefs() {
    this.columnDefs = [
      {headerName: "CHR", field: "chr"},
      {headerName: "Pos", field: "pos"},
      {headerName: "Ref", field: "ref"},
      {headerName: "Alt", field: "alt"},
      {headerName: "Samples", field: "samples"},
    ];
  }

}
