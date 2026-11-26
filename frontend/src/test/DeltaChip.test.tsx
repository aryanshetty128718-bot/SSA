import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DeltaChip } from '../components/DeltaChip';

describe('DeltaChip component', () => {
  it('formats positive improvements for lower-is-better metrics (e.g. sugars)', () => {
    render(
      <DeltaChip
        parameter="sugars"
        delta={-5.2}
        unit="g"
      />
    );

    expect(screen.getByLabelText(/sugars difference: -5.2g/i)).toBeInTheDocument();
    expect(screen.getByText(/sugars/i)).toBeInTheDocument();
    expect(screen.getByText(/-5.2g/)).toBeInTheDocument();
  });

  it('formats positive improvements for higher-is-better metrics (e.g. fiber)', () => {
    render(
      <DeltaChip
        parameter="fiber"
        delta={3.0}
        unit="g"
      />
    );

    expect(screen.getByLabelText(/fiber difference: \+3.0g/i)).toBeInTheDocument();
    expect(screen.getByText(/fiber/i)).toBeInTheDocument();
    expect(screen.getByText(/\+3.0g/)).toBeInTheDocument();
  });

  it('formats deterioration with rose badge', () => {
    render(
      <DeltaChip
        parameter="saturated_fat"
        delta={4.5}
        unit="g"
      />
    );

    const chip = screen.getByLabelText(/saturated_fat difference: \+4.5g/i);
    expect(chip).toBeInTheDocument();
    expect(chip.className).toContain('text-rose-800');
  });

  it('renders neutral badge for zero delta', () => {
    render(
      <DeltaChip
        parameter="energy"
        delta={0}
        unit="kcal"
      />
    );

    expect(screen.getByText(/energy: unchanged/i)).toBeInTheDocument();
  });
});
