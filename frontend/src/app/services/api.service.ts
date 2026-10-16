import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';

export interface County {
  id: number;
  name: string;
  code: string;
  capital: string;
  population?: number;
  area_km2?: number;
}

export interface Facility {
  id: number;
  name: string;
  type: string;
  county: string;
  latitude: number;
  longitude: number;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = environment.apiBase;

  constructor(private http: HttpClient) {}

  getCounties(): Promise<County[]> {
    return firstValueFrom(this.http.get<County[]>(`${this.base}/counties`));
  }

  getBoundaries(): Promise<any> {
    return firstValueFrom(this.http.get<any>(`${this.base}/boundaries/counties?tolerance=0.01`));
  }

  getSublocations(county?: string): Promise<any> {
    const url = county
      ? `${this.base}/sublocations?county=${encodeURIComponent(county)}`
      : `${this.base}/sublocations`;
    return firstValueFrom(this.http.get<any>(url));
  }

  getFacilities(county?: string, type?: string): Promise<Facility[]> {
    const params = new URLSearchParams();
    if (county) params.set('county', county);
    if (type) params.set('type', type);
    const qs = params.toString();
    return firstValueFrom(this.http.get<Facility[]>(`${this.base}/facilities${qs ? '?' + qs : ''}`));
  }

  getNearestFacility(lat: number, lon: number, type: string = 'hospital'): Promise<any> {
    const url = `${this.base}/facilities/nearest?lat=${lat}&lon=${lon}&type=${type}`;
    return firstValueFrom(this.http.get<any>(url));
  }

  getRoads(bbox?: { minLat: number; maxLat: number; minLon: number; maxLon: number }): Promise<any> {
    let url = `${this.base}/roads?limit=3000`;
    if (bbox) {
      url += `&min_lat=${bbox.minLat}&max_lat=${bbox.maxLat}&min_lon=${bbox.minLon}&max_lon=${bbox.maxLon}`;
    }
    return firstValueFrom(this.http.get<any>(url));
  }

  getCountyStats(id: number): Promise<any> {
    return firstValueFrom(this.http.get<any>(`${this.base}/counties/${id}/stats`));
  }

  health(): Promise<any> {
    return firstValueFrom(this.http.get(`${this.base}/health`));
  }
}
