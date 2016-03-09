import {Injectable} from 'angular2/core';
import {Http, Response} from 'angular2/http';
import {Observable} from 'rxjs/Observable';

@Injectable()
export class VariantsService {
  constructor (private http: Http) {}

  private _variantsUrl = '/api/variant';  // URL to web api

  getVariants () {
    return this.http.get(this._variantsUrl)
                    .map(res => res.json())
                    .catch(this.handleError);
  }
  private handleError (error: Response) {
    // in a real world app, we may send the error to some remote logging infrastructure
    // instead of just logging it to the console
    console.error(error);
    return Observable.throw(error.json().error || 'Server error');
  }
}