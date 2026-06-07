import "@gridz/react/styles.css";
import { Grid } from "../GridClient";
import { loadGrid } from "../../lib/loadGrid";

/**
 * Renders any subject: /kevin.gridz.eth, /did:pkh:eip155:1:0x...  Reads from ENS
 * (the GridzResolver), falls back to a Postgres projection. Every cell shows a
 * verification badge a visitor can re-check independently.
 */
export default async function SubjectPage({ params }: { params: Promise<{ subject: string }> }) {
  const { subject } = await params;
  const grid = await loadGrid(decodeURIComponent(subject));
  if (!grid) {
    return <main style={{ padding: 24 }}>No Gridz profile found for {decodeURIComponent(subject)}.</main>;
  }
  return <Grid grid={grid} />;
}
