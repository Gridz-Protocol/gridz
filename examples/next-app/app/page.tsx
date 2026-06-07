"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

/** Setup screen — no hard-coded subject. Enter the name/DID you want to render. */
export default function Home() {
  const [subject, setSubject] = useState("");
  const router = useRouter();
  return (
    <main style={{ padding: 24, maxWidth: 480, margin: "0 auto" }}>
      <h1>Gridz</h1>
      <p>Enter an ENS name (e.g. <code>kevin.gridz.eth</code>) or a DID to render its profile.</p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          if (subject.trim()) router.push(`/${encodeURIComponent(subject.trim())}`);
        }}
      >
        <input
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="kevin.gridz.eth"
          style={{ width: "100%", padding: 10 }}
        />
        <button type="submit" style={{ marginTop: 10, padding: "8px 16px" }}>Render</button>
      </form>
    </main>
  );
}
