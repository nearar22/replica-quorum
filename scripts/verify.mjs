import { readFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { createClient } from "genlayer-js";
import { studioDevnet } from "genlayer-js/chains";

const address=process.env.CONTRACT_ADDRESS?.trim();if(!address)throw new Error("CONTRACT_ADDRESS is required");const chain={...studioDevnet,id:61997,rpcUrls:{default:{http:["https://studio-next.genlayer.com/api"]}}};const client=createClient({chain});
const local=readFileSync(new URL("../contracts/replica_quorum.py",import.meta.url),"utf8"),deployed=await client.getContractCode(address),sha=value=>createHash("sha256").update(value).digest("hex");console.log(`LOCAL_SHA256=${sha(local)}\nDEPLOYED_SHA256=${sha(deployed)}\nSOURCE_MATCH=${local===deployed}`);if(local!==deployed)throw new Error("Source mismatch");
