import { describe, expect, it } from 'vitest';
import {
  isUuid,
  shortMoLabel,
  shortEntityName,
  utilBarColor,
  statusFromAtRisk,
  statusFromScore,
  statusFromUtil,
  statusFromOtd,
} from '@/lib/planningLabels';

describe('planningLabels.isUuid', () => {
  it('recognises a canonical v4 UUID', () => {
    expect(isUuid('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')).toBe(true);
  });

  it('is case-insensitive', () => {
    expect(isUuid('A0EEBC99-9C0B-4EF8-BB6D-6BB9BD380A11')).toBe(true);
  });

  it('rejects short strings, empty, and null', () => {
    expect(isUuid('MO-12345')).toBe(false);
    expect(isUuid('')).toBe(false);
    expect(isUuid(null)).toBe(false);
    expect(isUuid(undefined)).toBe(false);
  });

  it('rejects near-miss uuids', () => {
    expect(isUuid('a0eebc99-9c0b-4ef8-bb6d')).toBe(false);
    expect(isUuid('zzzeebc99-9c0b-4ef8-bb6d-6bb9bd380a11')).toBe(false);
  });
});

describe('planningLabels.shortMoLabel', () => {
  it('prefers a friendly ERP MO id when available', () => {
    expect(shortMoLabel('MO-1023', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')).toBe('MO-1023');
  });

  it('falls back to MO- + last 6 chars of UUID when ERP id is a UUID', () => {
    const label = shortMoLabel('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', null);
    expect(label).toBe('MO-380A11');
  });

  it('uses the mo_id UUID tail when ERP id is missing', () => {
    expect(shortMoLabel(null, 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd3800fe')).toBe('MO-3800FE');
  });

  it('renders a placeholder when both ids are missing', () => {
    expect(shortMoLabel(null, null)).toBe('MO-—');
    expect(shortMoLabel('', '')).toBe('MO-—');
  });

  it('keeps short ERP ids as-is even when they look non-UUID', () => {
    expect(shortMoLabel('SO-42', null)).toBe('SO-42');
  });
});

describe('planningLabels.shortEntityName', () => {
  it('returns the friendly name when it is not a UUID', () => {
    expect(shortEntityName('DT-500-Alpha', 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11')).toBe('DT-500-Alpha');
  });

  it('falls back to a MO- tail label when the name itself is a UUID', () => {
    const label = shortEntityName(
      'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
      'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    );
    expect(label).toBe('MO-380A11');
  });

  it('returns an em-dash when no data is available', () => {
    expect(shortEntityName(null, null)).toBe('—');
    expect(shortEntityName(undefined, undefined)).toBe('—');
  });
});

describe('planningLabels utilisation & status helpers', () => {
  it('utilBarColor thresholds', () => {
    // SPC-aligned: green ≤85, amber >85 and ≤90, red >90
    expect(utilBarColor(97)).toBe('#d03b3b');
    expect(utilBarColor(86)).toBe('#eda100');
    expect(utilBarColor(85)).toBe('#0ca30c');
    expect(utilBarColor(50)).toBe('#0ca30c');
  });

  it('statusFromAtRisk maps counts to health tiers', () => {
    expect(statusFromAtRisk(0)).toBe('healthy');
    expect(statusFromAtRisk(2)).toBe('warning');
    expect(statusFromAtRisk(10)).toBe('critical');
  });

  it('statusFromScore treats 80+ as healthy and <60 as critical', () => {
    expect(statusFromScore(95)).toBe('healthy');
    expect(statusFromScore(70)).toBe('warning');
    expect(statusFromScore(50)).toBe('critical');
  });

  it('statusFromUtil escalates >95 to critical', () => {
    expect(statusFromUtil(100)).toBe('critical');
    expect(statusFromUtil(90)).toBe('warning');
    expect(statusFromUtil(70)).toBe('healthy');
  });

  it('statusFromOtd treats 90+ as healthy and <80 as critical', () => {
    expect(statusFromOtd(95)).toBe('healthy');
    expect(statusFromOtd(85)).toBe('warning');
    expect(statusFromOtd(70)).toBe('critical');
  });
});
