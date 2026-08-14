declare module 'frappe-gantt' {
  export interface GanttTask {
    id: string;
    name: string;
    start: string;
    end: string;
    progress?: number;
    dependencies?: string;
    custom_class?: string;
  }

  export interface GanttOptions {
    view_mode?: string;
    view_mode_select?: boolean;
    bar_height?: number;
    padding?: number;
    on_click?: (task: GanttTask) => void;
    [key: string]: unknown;
  }

  export default class Gantt {
    constructor(wrapper: string | HTMLElement, tasks: GanttTask[], options?: GanttOptions);
    change_view_mode(mode?: string, maintain?: boolean): void;
    refresh(tasks: GanttTask[]): void;
  }
}

declare module 'frappe-gantt/dist/frappe-gantt.css';
