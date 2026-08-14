/**
 * React wrapper around frappe-gantt (MIT) — STREAM-5.1
 */
import { useEffect, useRef } from 'react';
import Gantt from 'frappe-gantt';
import 'frappe-gantt/dist/frappe-gantt.css';
import type { FrappeGanttTask } from '../ganttAdapter';

interface Props {
  tasks: FrappeGanttTask[];
  viewMode?: 'Day' | 'Week';
  onTaskClick?: (task: FrappeGanttTask) => void;
  className?: string;
}

export function FrappeGanttChart({ tasks, viewMode = 'Week', onTaskClick, className }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const ganttRef = useRef<InstanceType<typeof Gantt> | null>(null);
  const onClickRef = useRef(onTaskClick);
  onClickRef.current = onTaskClick;

  useEffect(() => {
    if (!containerRef.current || tasks.length === 0) return;

    containerRef.current.innerHTML = '';
    const el = document.createElement('div');
    el.id = 'ipe-frappe-gantt';
    containerRef.current.appendChild(el);

    // Strip _meta for library; keep lookup map
    const byId = new Map(tasks.map((t) => [t.id, t]));
    const libTasks = tasks.map(({ id, name, start, end, progress, custom_class }) => ({
      id,
      name,
      start,
      end,
      progress,
      custom_class,
    }));

    try {
      ganttRef.current = new Gantt(el, libTasks, {
        view_mode: viewMode,
        view_mode_select: false,
        bar_height: 24,
        padding: 14,
        on_click: (task: { id: string }) => {
          const full = byId.get(task.id);
          if (full) onClickRef.current?.(full);
        },
      });
    } catch (err) {
      console.error('frappe-gantt init failed', err);
    }

    return () => {
      ganttRef.current = null;
      if (containerRef.current) containerRef.current.innerHTML = '';
    };
  }, [tasks, viewMode]);

  return (
    <div
      ref={containerRef}
      className={className}
      data-testid="frappe-gantt"
      style={{ minHeight: 320, width: '100%', overflow: 'auto' }}
    />
  );
}
