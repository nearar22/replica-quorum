import { readFileSync } from "node:fs";
import { createAccount, createClient } from "genlayer-js";
import { studioDevnet } from "genlayer-js/chains";

const raw=process.env.GENLAYER_PRIVATE_KEY?.trim().replace(/^['"]|['"]$/g,"");if(!raw)throw new Error("GENLAYER_PRIVATE_KEY is required");
const keeper=setInterval(()=>{},60000),sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));const key=raw.startsWith("0x")?raw:`0x${raw}`;
const chain={...studioDevnet,id:61997,name:"GenLayer Studio Next",rpcUrls:{default:{http:["https://studio-next.genlayer.com/api"]}}};const client=createClient({chain,account:createAccount(key)});
async function finalized(hash){for(let attempt=0;attempt<240;attempt++){const receipt=await client.getTransaction({hash}).catch(()=>null);const status=String(receipt?.statusName??receipt?.status??"PENDING").toUpperCase();if(status==="FINALIZED")return receipt;if(["UNDETERMINED","DECLINED","CANCELED","CANCELLED"].includes(status))throw new Error(`Deployment ended ${status}`);await sleep(3000)}throw new Error("Deployment timed out before FINALIZED")}
const code=new Uint8Array(readFileSync(new URL("../contracts/replica_quorum.py",import.meta.url)));const fees=await client.estimateTransactionFees({leaderTimeunitsAllocation:250n,validatorTimeunitsAllocation:500n});
const hash=await client.deployContract({code,args:[],fees});console.log(`DEPLOY_TX=${hash}`);const receipt=await finalized(hash),status=String(receipt.statusName??receipt.status??"unknown"),execution=String(receipt.txExecutionResultName??receipt.txExecutionResult??"unknown"),consensus=String(receipt.resultName??receipt.result_name??"unknown");
console.log(`STATUS=${status};EXECUTION_RESULT=${execution};CONSENSUS=${consensus}`);if(status!=="FINALIZED"||execution!=="FINISHED_WITH_RETURN"||consensus==="MAJORITY_DISAGREE")throw new Error("Deployment failed");const address=receipt?.data?.contract_address??receipt?.txDataDecoded?.contractAddress??receipt?.to_address;if(!address)throw new Error("Missing contract address");console.log(`CONTRACT_ADDRESS=${address}`);clearInterval(keeper);
