"use client";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <html lang="en"><body style={{ margin: 32, fontFamily: "Arial, sans-serif", color: "#20242d", background: "#f7f8fa" }}><main role="alert"><h1>Unable to open the workspace</h1><p>Please reload the page or try again.</p><button onClick={reset}>Try again</button></main></body></html>;
}
