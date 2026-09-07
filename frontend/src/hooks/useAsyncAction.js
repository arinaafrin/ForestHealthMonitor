import { useCallback, useState } from "react";

export function useAsyncAction(asyncFunction) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);

  const run = useCallback(
    async (...args) => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await asyncFunction(...args);
        setData(result);
        return result;
      } catch (err) {
        setError(err.message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [asyncFunction]
  );

  return { run, isLoading, error, data, setError };
}
