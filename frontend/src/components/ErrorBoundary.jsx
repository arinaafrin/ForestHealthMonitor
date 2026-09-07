import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error("Unexpected UI error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="max-w-md mx-auto mt-16 p-6 bg-white rounded-lg shadow text-center">
          <p className="text-severe font-semibold mb-2">Something went wrong.</p>
          <p className="text-sm text-gray-600 mb-4">
            Please refresh the page. If this keeps happening, the backend may be unreachable.
          </p>
          <button
            className="px-4 py-2 bg-forest text-white rounded"
            onClick={() => window.location.reload()}
          >
            Refresh
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
