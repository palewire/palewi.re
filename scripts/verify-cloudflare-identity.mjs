let output = "";
for await (const chunk of process.stdin) {
  output += chunk;
}

let identity;
let validJson = true;
try {
  identity = JSON.parse(output);
} catch {
  console.error("Cloudflare authentication could not be verified: cf auth whoami returned invalid JSON.");
  process.exitCode = 1;
  validJson = false;
}

if (validJson) {
  if (!identity || typeof identity !== "object" || Array.isArray(identity)) {
    console.error("Cloudflare authentication could not be verified: cf auth whoami returned invalid identity data.");
    process.exitCode = 1;
  } else if (identity.authenticated !== true) {
    console.error(
      "Cloudflare authentication failed: cf reports that you are not logged in. " +
        "Run 'npm exec -- cf auth login' or set CLOUDFLARE_API_TOKEN.",
    );
    process.exitCode = 1;
  } else if (identity.tokenValid !== true) {
    console.error(
      "Cloudflare authentication failed: cf could not validate the Cloudflare token. " +
        "Run 'npm exec -- cf auth login' or set CLOUDFLARE_API_TOKEN.",
    );
    process.exitCode = 1;
  } else {
    console.log("Cloudflare authentication verified.");
  }
}
