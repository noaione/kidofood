const path = require("path");
const crossSpawn = require("cross-spawn");

const isWin = process.platform === "win32";

async function actualCode(args) {
    const python = path.resolve(
        __dirname,
        ".venv",
        isWin ? "Scripts" : "bin",
        "python"
    )
    const prom = new Promise((resolve, reject) => {
        const child = crossSpawn(python, args, {
            stdio: "inherit"
        });
        child.on("close", resolve);
        child.on("error", reject);
    })
    return prom;
}

function main() {
    const processArgs = process.argv.slice(2);
    actualCode(processArgs).then((code) => {
        process.exit(code);
    }
    ).catch((err) => {
        console.error(err);
        process.exit(1);
    });
}
main();