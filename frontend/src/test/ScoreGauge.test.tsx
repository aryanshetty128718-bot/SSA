import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ScoreGauge } from '../components/ScoreGauge';

describe('ScoreGauge component', () => {
  it('renders Excellent Choice band for score >= 80', () => {
    render(<ScoreGauge score={85} />);
    expect(screen.getByText('85.0')).toBeInTheDocument();
    expect(screen.getByText(/Excellent Choice/i)).toBeInTheDocument();
  });

  it('renders Healthy Choice band for score between 65 and 79.9', () => {
    render(<ScoreGauge score={72} />);
    expect(screen.getByText('72.0')).toBeInTheDocument();
    expect(screen.getByText(/Healthy Choice/i)).toBeInTheDocument();
  });

  it('renders Moderate band for score between 50 and 64.9', () => {
    render(<ScoreGauge score={58} />);
    expect(screen.getByText('58.0')).toBeInTheDocument();
    const badges = screen.getAllByText(/Moderate/i);
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });

  it('renders Less Healthy band for score between 35 and 49.9', () => {
    render(<ScoreGauge score={42} />);
    expect(screen.getByText('42.0')).toBeInTheDocument();
    expect(screen.getByText(/Less Healthy/i)).toBeInTheDocument();
  });

  it('renders Unhealthy / Ultra-Processed band for score < 35', () => {
    render(<ScoreGauge score={25} />);
    expect(screen.getByText('25.0')).toBeInTheDocument();
    expect(screen.getByText(/Unhealthy \/ Ultra-Processed/i)).toBeInTheDocument();
  });

  it('displays Insufficient Data when score is null', () => {
    render(<ScoreGauge score={null} />);
    expect(screen.getByText('N/A')).toBeInTheDocument();
    expect(screen.getByText(/Insufficient Data/i)).toBeInTheDocument();
  });
});
