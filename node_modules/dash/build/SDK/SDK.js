"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = exports.SDK = void 0;
/* eslint-disable no-restricted-exports */
// TODO remove default export
const dapi_client_1 = __importDefault(require("@dashevo/dapi-client"));
const wallet_lib_1 = require("@dashevo/wallet-lib");
const Client_1 = require("./Client");
const Core_1 = require("./Core");
const Platform_1 = require("./Platform");
const StateTransitionBroadcastError_1 = require("../errors/StateTransitionBroadcastError");
var SDK;
(function (SDK) {
    SDK.DAPIClient = dapi_client_1.default;
    SDK.Client = Client_1.Client;
    SDK.Core = Core_1.Core;
    SDK.Platform = Platform_1.Platform;
    // Wallet-lib primitives
    SDK.Wallet = wallet_lib_1.Wallet;
    SDK.Account = wallet_lib_1.Account;
    SDK.KeyChain = wallet_lib_1.DerivableKeyChain;
    // TODO: consider merging into Wallet above and mark as DEPRECATED
    SDK.WalletLib = {
        CONSTANTS: wallet_lib_1.CONSTANTS,
        EVENTS: wallet_lib_1.EVENTS,
        plugins: wallet_lib_1.plugins,
        utils: wallet_lib_1.utils,
    };
    SDK.PlatformProtocol = SDK.Platform.DashPlatformProtocol;
    SDK.Essentials = {
        Buffer,
    };
    SDK.Errors = {
        StateTransitionBroadcastError: StateTransitionBroadcastError_1.StateTransitionBroadcastError,
    };
})(SDK = exports.SDK || (exports.SDK = {}));
exports.default = SDK;
//# sourceMappingURL=SDK.js.map