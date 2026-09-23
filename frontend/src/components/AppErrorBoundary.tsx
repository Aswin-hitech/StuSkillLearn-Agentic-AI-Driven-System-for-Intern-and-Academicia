import React from 'react';

type State = { failed: boolean; message: string };

export class AppErrorBoundary extends React.Component<React.PropsWithChildren, State> {
  state: State = { failed: false, message: '' };

  static getDerivedStateFromError(error: unknown): State {
    return {
      failed: true,
      message: error instanceof Error ? error.message : 'An unexpected client error occurred.',
    };
  }

  componentDidCatch(error: unknown, info: React.ErrorInfo) {
    // Keep production UI recoverable without exposing stack traces to end users.
    // Structured browser telemetry can be connected here later (for example Sentry/OTel).
    console.error('StuSkillLink UI error', error, info.componentStack);
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <main className="grid min-h-screen place-items-center bg-slate-50 px-4">
        <section className="surface w-full max-w-lg p-7 text-center">
          <p className="eyebrow">Application recovery</p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-950">This page could not be rendered.</h1>
          <p className="mt-3 text-sm leading-6 text-slate-500">{this.state.message}</p>
          <button className="btn-primary mt-6" type="button" onClick={() => window.location.assign('/')}>Return to StuSkillLink</button>
        </section>
      </main>
    );
  }
}
