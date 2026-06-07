import { defineConfig } from "vocs";

export default defineConfig({
  title: "Gridz",
  description: "Cryptographically-attested social graphs for humans, AI agents, and organizations.",
  sidebar: [
    { text: "Introduction", link: "/" },
    { text: "Getting started", link: "/getting-started" },
    { text: "Concepts", link: "/concepts" },
    { text: "Verification", link: "/verification" },
    {
      text: "Reference",
      items: [
        { text: "Grid schema", link: "/reference/grid-schema" },
        { text: "Standard keys", link: "/reference/standard-keys" },
        { text: "Canonicalization", link: "/reference/canonicalization" },
      ],
    },
    { text: "Blog", items: [{ text: "Announcing Gridz", link: "/blog/announcing-gridz" }] },
  ],
});
