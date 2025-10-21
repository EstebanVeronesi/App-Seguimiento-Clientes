"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    Object.defineProperty(o, k2, { enumerable: true, get: function() { return m[k]; } });
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Platform = void 0;
const wasm_dpp_1 = __importStar(require("@dashevo/wasm-dpp"));
const crypto_1 = __importDefault(require("crypto"));
const createAssetLockTransaction_1 = __importDefault(require("./createAssetLockTransaction"));
const broadcast_1 = __importDefault(require("./methods/documents/broadcast"));
const create_1 = __importDefault(require("./methods/documents/create"));
const get_1 = __importDefault(require("./methods/documents/get"));
const publish_1 = __importDefault(require("./methods/contracts/publish"));
const update_1 = __importDefault(require("./methods/contracts/update"));
const create_2 = __importDefault(require("./methods/contracts/create"));
const get_2 = __importDefault(require("./methods/contracts/get"));
const history_1 = __importDefault(require("./methods/contracts/history"));
const get_3 = __importDefault(require("./methods/identities/get"));
const register_1 = __importDefault(require("./methods/identities/register"));
const topUp_1 = __importDefault(require("./methods/identities/topUp"));
const creditTransfer_1 = __importDefault(require("./methods/identities/creditTransfer"));
const creditWithdrawal_1 = __importDefault(require("./methods/identities/creditWithdrawal"));
const update_2 = __importDefault(require("./methods/identities/update"));
const createIdentityCreateTransition_1 = __importDefault(require("./methods/identities/internal/createIdentityCreateTransition"));
const createIdentityTopUpTransition_1 = __importDefault(require("./methods/identities/internal/createIdentityTopUpTransition"));
const createAssetLockProof_1 = __importDefault(require("./methods/identities/internal/createAssetLockProof"));
const waitForCoreChainLockedHeight_1 = __importDefault(require("./methods/identities/internal/waitForCoreChainLockedHeight"));
const register_2 = __importDefault(require("./methods/names/register"));
const resolve_1 = __importDefault(require("./methods/names/resolve"));
const resolveByRecord_1 = __importDefault(require("./methods/names/resolveByRecord"));
const search_1 = __importDefault(require("./methods/names/search"));
const broadcastStateTransition_1 = __importDefault(require("./broadcastStateTransition"));
const logger_1 = __importDefault(require("../../../logger"));
const Fetcher_1 = __importDefault(require("./Fetcher"));
const NonceManager_1 = __importDefault(require("./NonceManager/NonceManager"));
/**
 * Class for Dash Platform
 *
 * @param documents - documents
 * @param identities - identities
 * @param names - names
 * @param contracts - contracts
 */
class Platform {
    /**
       * Construct some instance of Platform
       *
       * @param {PlatformOpts} options - options for Platform
       */
    constructor(options) {
        this.documents = {
            broadcast: broadcast_1.default.bind(this),
            create: create_1.default.bind(this),
            get: get_1.default.bind(this),
        };
        this.contracts = {
            publish: publish_1.default.bind(this),
            update: update_1.default.bind(this),
            create: create_2.default.bind(this),
            get: get_2.default.bind(this),
            history: history_1.default.bind(this),
        };
        this.names = {
            register: register_2.default.bind(this),
            resolve: resolve_1.default.bind(this),
            resolveByRecord: resolveByRecord_1.default.bind(this),
            search: search_1.default.bind(this),
        };
        this.identities = {
            register: register_1.default.bind(this),
            get: get_3.default.bind(this),
            topUp: topUp_1.default.bind(this),
            creditTransfer: creditTransfer_1.default.bind(this),
            update: update_2.default.bind(this),
            withdrawCredits: creditWithdrawal_1.default.bind(this),
            utils: {
                createAssetLockProof: createAssetLockProof_1.default.bind(this),
                createAssetLockTransaction: createAssetLockTransaction_1.default.bind(this),
                createIdentityCreateTransition: createIdentityCreateTransition_1.default.bind(this),
                createIdentityTopUpTransition: createIdentityTopUpTransition_1.default.bind(this),
                waitForCoreChainLockedHeight: waitForCoreChainLockedHeight_1.default.bind(this),
            },
        };
        this.client = options.client;
        const walletId = this.client.wallet ? this.client.wallet.walletId : 'noid';
        this.logger = logger_1.default.getForId(walletId);
        // use protocol version from options if set
        if (options.driveProtocolVersion !== undefined) {
            this.protocolVersion = options.driveProtocolVersion;
        }
        this.fetcher = new Fetcher_1.default(this.client.getDAPIClient());
        this.nonceManager = new NonceManager_1.default(this.client.getDAPIClient());
    }
    /**
       * Broadcasts state transition
       * @param {Object} stateTransition
       */
    broadcastStateTransition(stateTransition) {
        return broadcastStateTransition_1.default(this, stateTransition);
    }
    async initialize() {
        if (!this.dpp) {
            await Platform.initializeDppModule();
            if (this.protocolVersion === undefined) {
                // use mapped protocol version otherwise
                // fallback to one that set in dpp as the last option
                const mappedProtocolVersion = Platform.networkToProtocolVersion.get(this.client.network);
                this.protocolVersion = mappedProtocolVersion !== undefined
                    ? mappedProtocolVersion : wasm_dpp_1.getLatestProtocolVersion();
            }
            // eslint-disable-next-line
            this.dpp = new wasm_dpp_1.DashPlatformProtocol({
                generate: () => crypto_1.default.randomBytes(32),
            }, this.protocolVersion);
        }
    }
    // Explicitly provide DPPModule as return type.
    // If we don't do it, typescript behaves weird and in compiled Platform.d.ts
    // this code looks like this.
    //
    // ```
    // static initializeDppModule(): Promise<typeof import("@dashevo/wasm-dppdist/dpp")>;
    // ```
    //
    // Slash is missing before `dist` and TS compilation in consumers is breaking
    static async initializeDppModule() {
        return wasm_dpp_1.default();
    }
}
exports.Platform = Platform;
Platform.networkToProtocolVersion = new Map([
    ['testnet', 1],
]);
//# sourceMappingURL=Platform.js.map