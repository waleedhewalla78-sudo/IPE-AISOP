import type { ReactNode } from 'react';
import { Component, type ErrorInfo } from 'react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackHint?: string;
}

interface State {
  hasError: boolean;
}

/** Feature-level error boundary so one panel crash does not take down the page. */
export class FeatureErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('[FeatureErrorBoundary]', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-6 text-sm text-red-800">
          <p className="font-medium">{this.props.fallbackTitle ?? 'This section failed to load.'}</p>
          <p className="mt-1 text-red-700/80">
            {this.props.fallbackHint ?? 'Other parts of the page should still work. Try refreshing.'}
          </p>
          <button
            type="button"
            className="mt-3 text-sm font-medium underline"
            onClick={() => this.setState({ hasError: false })}
          >
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
