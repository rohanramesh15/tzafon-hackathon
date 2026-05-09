import "./index.css";
import { createRoot } from "react-dom/client";
import { App } from "./App";

const rootEl = document.getElementById("root");
if (!rootEl) throw new Error('Missing root element "#root"');
createRoot(rootEl).render(<App />);
