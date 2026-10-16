import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class StateService {
  private theme$ = new BehaviorSubject<'light' | 'dark'>('light');
  private sidebarOpen$ = new BehaviorSubject<boolean>(true);

  theme = this.theme$.asObservable();
  sidebarOpen = this.sidebarOpen$.asObservable();

  toggleTheme() {
    this.theme$.next(this.theme$.value === 'light' ? 'dark' : 'light');
  }

  toggleSidebar() {
    this.sidebarOpen$.next(!this.sidebarOpen$.value);
  }

  get currentTheme() { return this.theme$.value; }
}
