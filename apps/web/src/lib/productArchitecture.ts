/**
 * IPE hybrid product architecture — Manufacturing APS + Enterprise OS shell.
 * Source of truth for domain rail + secondary module sidebars.
 *
 * STREAM 3 primary rail: Home · Plan · Execute · Supply · Analyze · Copilot
 * (+ Admin gear pinned at bottom). Legacy domain ids alias to these.
 */
import {
  Home,
  ClipboardList,
  Factory,
  Package,
  BarChart3,
  Sparkles,
  Settings,
  AlertTriangle,
  TrendingUp,
  GitBranch,
  CalendarClock,
  Layers,
  Activity,
  FolderKanban,
  CheckSquare,
  Calendar,
  FileText,
  BookOpen,
  Goal,
  Users,
  Zap,
  FileBarChart,
  MessageSquare,
  ClipboardCheck,
  type LucideIcon,
} from 'lucide-react';
import { ROUTES } from './constants';
import type { PersonaId } from './personaHome';

/** Primary rail domain ids (Star Trans demo nav). */
export type DomainId =
  | 'home'
  | 'plan'
  | 'execute'
  | 'supply'
  | 'analyze'
  | 'copilot'
  | 'admin';

/** Legacy ids retained so older call sites / tests can alias. */
export type LegacyDomainId = 'today' | 'decide' | 'work' | 'run' | 'ai' | 'govern';

export const DOMAIN_ID_ALIASES: Record<LegacyDomainId, DomainId> = {
  today: 'home',
  decide: 'analyze',
  work: 'execute',
  run: 'execute',
  ai: 'copilot',
  govern: 'admin',
};

export function normalizeDomainId(id: string): DomainId {
  if (id in DOMAIN_ID_ALIASES) return DOMAIN_ID_ALIASES[id as LegacyDomainId];
  return id as DomainId;
}

export interface DomainModule {
  id: string;
  to: string;
  labelKey: string;
  fallback: string;
  description?: string;
  match?: string;
}

export interface ProductDomain {
  id: DomainId;
  to: string;
  labelKey: string;
  fallback: string;
  icon: LucideIcon;
  /** When true, main content uses full width (no secondary sidebar). */
  fullBleed?: boolean;
  /** Pin to bottom of icon rail (Admin gear). */
  railBottom?: boolean;
  modules: DomainModule[];
}

export const PRODUCT_DOMAINS: ProductDomain[] = [
  {
    id: 'home',
    to: ROUTES.WORKSPACE,
    labelKey: 'nav.domain.home',
    fallback: 'Home',
    icon: Home,
    fullBleed: true,
    modules: [],
  },
  {
    id: 'plan',
    to: ROUTES.PLANNING_CONTROL_TOWER,
    labelKey: 'nav.domain.plan',
    fallback: 'Plan',
    icon: ClipboardList,
    modules: [
      {
        id: 'controlTower',
        to: ROUTES.PLANNING_CONTROL_TOWER,
        labelKey: 'nav.module.controlTower',
        fallback: 'Control Tower',
        description: 'Risk queue & bottlenecks',
      },
      {
        id: 'demand',
        to: ROUTES.PLANNING_DEMAND,
        labelKey: 'nav.module.demand',
        fallback: 'Demand Intelligence',
        description: 'Forecasts & sensing',
      },
      {
        id: 'resolution',
        to: ROUTES.PLANNING_RESOLUTION,
        labelKey: 'nav.module.resolution',
        fallback: 'Resolution Center',
        description: 'Decide & approve',
      },
      {
        id: 'schedule',
        to: ROUTES.PLANNING_SCHEDULE,
        labelKey: 'nav.module.schedule',
        fallback: 'Production Schedule',
        description: 'Gantt & AI solver',
      },
      {
        id: 'scenarios',
        to: ROUTES.PLANNING_SCENARIOS,
        labelKey: 'nav.module.scenarios',
        fallback: 'Scenario Workbench',
        description: 'What-if simulation',
      },
      {
        id: 'predictions',
        to: ROUTES.PLANNING_PREDICTIONS,
        labelKey: 'nav.module.predictions',
        fallback: 'Predictive Risk',
        description: '3 / 7 / 14-day horizons',
      },
      {
        id: 'planOverview',
        to: ROUTES.PLANNING_DASHBOARD,
        labelKey: 'nav.module.planOverview',
        fallback: 'Plan Overview',
        description: 'Hub summary',
      },
    ],
  },
  {
    id: 'execute',
    to: ROUTES.SHOP_FLOOR,
    labelKey: 'nav.domain.execute',
    fallback: 'Execute',
    icon: Factory,
    modules: [
      {
        id: 'shopFloor',
        to: ROUTES.SHOP_FLOOR,
        labelKey: 'nav.module.shopFloor',
        fallback: 'Shop Floor',
        description: 'Live work centers',
      },
      {
        id: 'equipment',
        to: ROUTES.COMMAND_EQUIPMENT,
        labelKey: 'nav.module.equipment',
        fallback: 'Equipment',
        description: 'Asset health',
      },
      {
        id: 'projects',
        to: ROUTES.WORK_PROJECTS,
        labelKey: 'nav.module.projects',
        fallback: 'Projects',
        description: 'Initiatives & stage gates',
      },
      {
        id: 'tasks',
        to: ROUTES.WORK_TASKS,
        labelKey: 'nav.module.tasks',
        fallback: 'Tasks',
        description: 'Assignments linked to MOs',
      },
      {
        id: 'approvals',
        to: ROUTES.WORK_APPROVALS,
        labelKey: 'nav.module.approvals',
        fallback: 'Approvals',
        description: 'Resolutions & scenarios',
      },
      {
        id: 'meetings',
        to: ROUTES.WORK_MEETINGS,
        labelKey: 'nav.module.meetings',
        fallback: 'Meetings',
        description: 'Prep packs & agendas',
      },
      {
        id: 'calendar',
        to: ROUTES.WORK_CALENDAR,
        labelKey: 'nav.module.calendar',
        fallback: 'Calendar',
        description: 'Planning & shifts',
      },
      {
        id: 'documents',
        to: ROUTES.WORK_DOCUMENTS,
        labelKey: 'nav.module.documents',
        fallback: 'Documents',
        description: 'Plans, attachments',
      },
      {
        id: 'knowledge',
        to: ROUTES.WORK_KNOWLEDGE,
        labelKey: 'nav.module.knowledge',
        fallback: 'Knowledge',
        description: 'SOPs & playbooks',
      },
      {
        id: 'objectives',
        to: ROUTES.WORK_OBJECTIVES,
        labelKey: 'nav.module.objectives',
        fallback: 'Objectives',
        description: 'OKRs & cascades',
      },
      {
        id: 'kpis',
        to: ROUTES.WORK_KPIS,
        labelKey: 'nav.module.kpis',
        fallback: 'KPIs',
        description: 'Scorecards',
      },
      {
        id: 'teams',
        to: ROUTES.WORK_TEAMS,
        labelKey: 'nav.module.teams',
        fallback: 'Teams',
        description: 'Coverage & roles',
      },
      {
        id: 'automation',
        to: ROUTES.WORK_AUTOMATION,
        labelKey: 'nav.module.automation',
        fallback: 'Automation',
        description: 'Agents & rules',
      },
      {
        id: 'reports',
        to: ROUTES.WORK_REPORTS,
        labelKey: 'nav.module.reports',
        fallback: 'Reports',
        description: 'Executive packs',
      },
    ],
  },
  {
    id: 'supply',
    to: ROUTES.SUPPLY_PLANNING,
    labelKey: 'nav.domain.supply',
    fallback: 'Supply',
    icon: Package,
    modules: [
      {
        id: 'materials',
        to: ROUTES.SUPPLY_PLANNING,
        labelKey: 'nav.module.materials',
        fallback: 'Supply Planning',
        description: 'Netting, ATP, procurement',
      },
      {
        id: 'inventory',
        to: ROUTES.SUPPLY_INVENTORY,
        labelKey: 'nav.module.inventory',
        fallback: 'Inventory',
        description: 'Stock & buffers',
      },
      {
        id: 'procurement',
        to: ROUTES.SUPPLY_PROCUREMENT,
        labelKey: 'nav.module.procurement',
        fallback: 'Procurement',
        description: 'Buy & RFQs',
      },
      {
        id: 'suppliers',
        to: ROUTES.SUPPLY_SUPPLIERS,
        labelKey: 'nav.module.suppliers',
        fallback: 'Suppliers',
        description: 'Scorecards',
      },
    ],
  },
  {
    id: 'analyze',
    to: ROUTES.COMMAND_DASHBOARD,
    labelKey: 'nav.domain.analyze',
    fallback: 'Analyze',
    icon: BarChart3,
    modules: [
      {
        id: 'outcomes',
        to: ROUTES.COMMAND_DASHBOARD,
        labelKey: 'nav.module.outcomes',
        fallback: 'Outcomes & Risk',
        description: 'Executive pulse and action queue',
        match: ROUTES.COMMAND_DASHBOARD,
      },
      {
        id: 'warRoom',
        to: ROUTES.COMMAND_WAR_ROOM,
        labelKey: 'nav.module.warRoom',
        fallback: 'War Room',
        description: 'Active disruptions',
      },
      {
        id: 'costOfChaos',
        to: ROUTES.COMMAND_COST_OF_CHAOS,
        labelKey: 'nav.module.costOfChaos',
        fallback: 'Cost of Chaos',
        description: 'Financial exposure',
      },
      {
        id: 'executive',
        to: ROUTES.COMMAND_EXECUTIVE,
        labelKey: 'nav.module.executive',
        fallback: 'Executive',
        description: 'P&L and S&OP',
      },
      {
        id: 'otd',
        to: ROUTES.COMMAND_OTD_ANALYTICS,
        labelKey: 'nav.module.otd',
        fallback: 'OTD Analytics',
        description: 'Delivery performance',
      },
      {
        id: 'opsLive',
        to: ROUTES.COMMAND_OPS_LIVE,
        labelKey: 'nav.module.opsLive',
        fallback: 'Ops Live',
        description: 'Real-time operations',
      },
      {
        id: 'intelligence',
        to: ROUTES.INTELLIGENCE,
        labelKey: 'nav.module.intelligence',
        fallback: 'Intelligence',
        description: 'Deep analytics',
        match: ROUTES.INTELLIGENCE,
      },
    ],
  },
  {
    id: 'copilot',
    to: ROUTES.AI_COPILOT,
    labelKey: 'nav.domain.copilot',
    fallback: 'Copilot',
    icon: Sparkles,
    modules: [
      {
        id: 'copilot',
        to: ROUTES.AI_COPILOT,
        labelKey: 'nav.module.copilot',
        fallback: 'Copilot',
        description: 'Ask the planning engine',
      },
      {
        id: 'agents',
        to: ROUTES.PLATFORM_AGENTS,
        labelKey: 'nav.module.agents',
        fallback: 'Agents',
        description: 'A1–A17 intelligence roster',
      },
      {
        id: 'meetingPrep',
        to: ROUTES.AI_MEETING_PREP,
        labelKey: 'nav.module.meetingPrep',
        fallback: 'Meeting Prep',
        description: 'Briefing packs',
      },
      {
        id: 'designAi',
        to: ROUTES.AI_DESIGN,
        labelKey: 'nav.module.designAi',
        fallback: 'Design AI',
        description: 'Engineering assist',
      },
    ],
  },
  {
    id: 'admin',
    to: ROUTES.PLATFORM_ADMIN,
    labelKey: 'nav.domain.admin',
    fallback: 'Admin',
    icon: Settings,
    railBottom: true,
    modules: [
      {
        id: 'govOverview',
        to: ROUTES.AI_OVERVIEW,
        labelKey: 'nav.module.govOverview',
        fallback: 'Governance Overview',
        description: 'Health & priority queue',
      },
      {
        id: 'aiTrust',
        to: ROUTES.AI_TRUST,
        labelKey: 'nav.module.aiTrust',
        fallback: 'AI Trust',
        description: 'Shadow mode & adoption',
      },
      {
        id: 'compliance',
        to: ROUTES.AI_COMPLIANCE,
        labelKey: 'nav.module.compliance',
        fallback: 'Compliance',
        description: 'SOC2 / GDPR',
      },
      {
        id: 'quality',
        to: ROUTES.AI_QUALITY,
        labelKey: 'nav.module.quality',
        fallback: 'Quality',
        description: 'SPC & COPQ',
      },
      {
        id: 'mdr',
        to: ROUTES.AI_MDR,
        labelKey: 'nav.module.mdr',
        fallback: 'MDR Gate',
        description: 'Model risk',
      },
      {
        id: 'platform',
        to: ROUTES.PLATFORM_ADMIN,
        labelKey: 'nav.module.platform',
        fallback: 'Platform Admin',
        description: 'Tenant & connectors',
      },
      {
        id: 'upload',
        to: ROUTES.PLATFORM_UPLOAD,
        labelKey: 'nav.module.upload',
        fallback: 'Data Upload',
        description: 'CDM commit',
      },
      {
        id: 'customerPortal',
        to: ROUTES.CUSTOMER_PORTAL,
        labelKey: 'nav.module.customerPortal',
        fallback: 'Customer Portal',
        description: 'External SCN view',
      },
    ],
  },
];

function domainById(id: DomainId): ProductDomain {
  return PRODUCT_DOMAINS.find((d) => d.id === id) ?? PRODUCT_DOMAINS[0];
}

/** Resolve active domain from pathname (prefix-first, APS + Work OS). */
export function resolveDomain(pathname: string): ProductDomain {
  if (pathname === ROUTES.WORKSPACE || pathname === '/') return domainById('home');
  if (pathname === ROUTES.WORK || pathname.startsWith(`${ROUTES.WORK}/`)) {
    return domainById('execute');
  }
  if (pathname === ROUTES.SHOP_FLOOR || pathname.startsWith(`${ROUTES.SHOP_FLOOR}/`)) {
    return domainById('execute');
  }
  if (pathname.startsWith(ROUTES.COMMAND_EQUIPMENT)) return domainById('execute');
  if (pathname.startsWith(ROUTES.COMMAND_CENTER)) return domainById('analyze');
  if (pathname.startsWith(ROUTES.SUPPLY_CHAIN)) return domainById('supply');
  if (pathname.startsWith(ROUTES.PLANNING)) return domainById('plan');
  if (pathname.startsWith(ROUTES.PLATFORM_AGENTS)) return domainById('copilot');
  if (pathname.startsWith(ROUTES.AI_GOVERNANCE)) {
    const aiPaths = [ROUTES.AI_COPILOT, ROUTES.AI_MEETING_PREP, ROUTES.AI_DESIGN];
    if (aiPaths.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
      return domainById('copilot');
    }
    return domainById('admin');
  }
  if (pathname.startsWith(ROUTES.INTELLIGENCE)) return domainById('analyze');
  if (pathname.startsWith(ROUTES.PLATFORM) || pathname.startsWith(ROUTES.CUSTOMER_PORTAL)) {
    return domainById('admin');
  }
  return domainById('home');
}

/** Icons for Work module cards (page scaffolds). */
export const WORK_MODULE_ICONS: Record<string, LucideIcon> = {
  projects: FolderKanban,
  tasks: CheckSquare,
  approvals: ClipboardCheck,
  meetings: MessageSquare,
  calendar: Calendar,
  documents: FileText,
  knowledge: BookOpen,
  objectives: Goal,
  kpis: BarChart3,
  teams: Users,
  automation: Zap,
  reports: FileBarChart,
  controlTower: AlertTriangle,
  demand: TrendingUp,
  resolution: GitBranch,
  schedule: CalendarClock,
  scenarios: Layers,
  predictions: Activity,
};

/**
 * Persona-ranked domain order (Home always first; Admin stays last via railBottom).
 */
const PERSONA_DOMAIN_ORDER: Record<PersonaId, DomainId[]> = {
  CEO: ['home', 'analyze', 'execute', 'plan', 'copilot', 'supply', 'admin'],
  Finance: ['home', 'analyze', 'execute', 'admin', 'plan', 'copilot', 'supply'],
  Ops: ['home', 'analyze', 'plan', 'execute', 'supply', 'copilot', 'admin'],
  Sales: ['home', 'analyze', 'plan', 'execute', 'copilot', 'admin', 'supply'],
  SC: ['home', 'supply', 'plan', 'analyze', 'execute', 'copilot', 'admin'],
  Material: ['home', 'supply', 'plan', 'analyze', 'execute', 'copilot', 'admin'],
  Production: ['home', 'plan', 'execute', 'analyze', 'supply', 'copilot', 'admin'],
  Scheduler: ['home', 'plan', 'analyze', 'execute', 'supply', 'copilot', 'admin'],
  Demand: ['home', 'plan', 'analyze', 'execute', 'copilot', 'admin', 'supply'],
  Frontline: ['home', 'execute', 'plan', 'copilot', 'analyze', 'supply', 'admin'],
};

/** Plan module priority per persona (unlisted modules keep relative order after). */
const PERSONA_PLAN_MODULE_ORDER: Record<PersonaId, string[]> = {
  CEO: ['controlTower', 'scenarios', 'predictions', 'demand', 'planOverview'],
  Finance: ['demand', 'scenarios', 'controlTower', 'predictions'],
  Ops: ['controlTower', 'resolution', 'schedule', 'predictions', 'scenarios'],
  Sales: ['demand', 'controlTower', 'scenarios', 'predictions'],
  SC: ['controlTower', 'demand', 'scenarios', 'predictions'],
  Material: ['controlTower', 'demand', 'scenarios'],
  Production: ['controlTower', 'resolution', 'schedule', 'predictions', 'scenarios', 'demand'],
  Scheduler: ['schedule', 'controlTower', 'resolution', 'scenarios', 'predictions'],
  Demand: ['demand', 'scenarios', 'controlTower', 'predictions', 'schedule'],
  Frontline: ['schedule', 'controlTower', 'resolution'],
};

const PERSONA_SUPPLY_MODULE_ORDER: Record<PersonaId, string[]> = {
  CEO: ['materials', 'inventory', 'procurement', 'suppliers'],
  Finance: ['procurement', 'suppliers', 'materials', 'inventory'],
  Ops: ['materials', 'inventory', 'procurement', 'suppliers'],
  Sales: ['materials', 'inventory'],
  SC: ['materials', 'inventory', 'procurement', 'suppliers'],
  Material: ['materials', 'inventory', 'procurement', 'suppliers'],
  Production: ['materials', 'inventory', 'procurement'],
  Scheduler: ['materials', 'inventory'],
  Demand: ['materials', 'inventory'],
  Frontline: ['materials', 'inventory'],
};

const PERSONA_EXECUTE_MODULE_ORDER: Record<PersonaId, string[]> = {
  CEO: ['objectives', 'kpis', 'reports', 'approvals', 'projects', 'meetings', 'shopFloor'],
  Finance: ['kpis', 'objectives', 'reports', 'approvals', 'projects'],
  Ops: ['shopFloor', 'tasks', 'approvals', 'projects', 'meetings', 'calendar', 'automation'],
  Sales: ['meetings', 'tasks', 'projects', 'calendar', 'documents'],
  SC: ['tasks', 'approvals', 'projects', 'documents', 'knowledge'],
  Material: ['tasks', 'approvals', 'documents', 'knowledge'],
  Production: ['shopFloor', 'tasks', 'approvals', 'calendar', 'knowledge', 'meetings'],
  Scheduler: ['shopFloor', 'tasks', 'calendar', 'approvals', 'projects'],
  Demand: ['projects', 'meetings', 'tasks', 'reports', 'objectives'],
  Frontline: ['shopFloor', 'tasks', 'calendar', 'knowledge', 'meetings'],
};

export function rankDomainsForPersona(persona: PersonaId): ProductDomain[] {
  const order = PERSONA_DOMAIN_ORDER[persona] ?? PERSONA_DOMAIN_ORDER.Ops;
  const byId = new Map(PRODUCT_DOMAINS.map((d) => [d.id, d]));
  const ranked: ProductDomain[] = [];
  for (const id of order) {
    const d = byId.get(id);
    if (d) ranked.push(d);
  }
  for (const d of PRODUCT_DOMAINS) {
    if (!ranked.some((r) => r.id === d.id)) ranked.push(d);
  }
  // Admin always last in the list (IconRail pins it visually at bottom).
  ranked.sort((a, b) => Number(a.railBottom) - Number(b.railBottom));
  return ranked;
}

export function rankModulesForPersona(
  domain: ProductDomain,
  persona: PersonaId,
): DomainModule[] {
  let order: string[] = [];
  if (domain.id === 'plan') order = PERSONA_PLAN_MODULE_ORDER[persona] ?? [];
  if (domain.id === 'execute') order = PERSONA_EXECUTE_MODULE_ORDER[persona] ?? [];
  if (domain.id === 'supply') order = PERSONA_SUPPLY_MODULE_ORDER[persona] ?? [];
  if (order.length === 0) return domain.modules;

  const priority = new Map(order.map((id, i) => [id, i]));
  return domain.modules.slice().sort((a, b) => {
    const pa = priority.has(a.id) ? (priority.get(a.id) as number) : 1000;
    const pb = priority.has(b.id) ? (priority.get(b.id) as number) : 1000;
    if (pa !== pb) return pa - pb;
    return a.id.localeCompare(b.id);
  });
}

/** Persona default landing inside Plan domain. */
export function planHomeForPersona(persona: PersonaId): string {
  switch (persona) {
    case 'Demand':
    case 'Sales':
      return ROUTES.PLANNING_DEMAND;
    case 'Scheduler':
      return ROUTES.PLANNING_SCHEDULE;
    case 'SC':
    case 'Material':
      // Supply has its own rail entry; Plan lands on Control Tower.
      return ROUTES.PLANNING_CONTROL_TOWER;
    case 'CEO':
    case 'Finance':
      return ROUTES.PLANNING_CONTROL_TOWER;
    default:
      return ROUTES.PLANNING_CONTROL_TOWER;
  }
}

