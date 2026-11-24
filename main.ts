import { copyFileSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const src = join(__dirname, "out", "entry.png");
const destDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const dest = join(destDir, "entry.png");

copyFileSync(src, dest);