import { copyFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const src = join(__dirname, "out", "entry.png");
const dest = join(process.env.MAKEFUN_OUTPUT_DIR!, "entry.png");

copyFileSync(src, dest);