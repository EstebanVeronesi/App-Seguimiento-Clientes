"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.creditTransfer = void 0;
const wasm_dpp_1 = require("@dashevo/wasm-dpp");
const broadcastStateTransition_1 = __importDefault(require("../../broadcastStateTransition"));
const signStateTransition_1 = require("../../signStateTransition");
async function creditTransfer(identity, recipientId, amount) {
    this.logger.debug(`[Identity#creditTransfer] credit transfer from ${identity.getId().toString()} to ${recipientId.toString()} with amount ${amount}`);
    await this.initialize();
    const { dpp } = this;
    recipientId = wasm_dpp_1.Identifier.from(recipientId);
    const identityNonce = await this.nonceManager.bumpIdentityNonce(identity.getId());
    const identityCreditTransferTransition = dpp.identity
        .createIdentityCreditTransferTransition(identity, recipientId, BigInt(amount), BigInt(identityNonce));
    this.logger.silly('[Identity#creditTransfer] Created IdentityCreditTransferTransition');
    const signerKeyIndex = 3;
    await signStateTransition_1.signStateTransition(this, identityCreditTransferTransition, identity, signerKeyIndex);
    // Skipping validation because it's already done above
    await broadcastStateTransition_1.default(this, identityCreditTransferTransition, {
        skipValidation: true,
    });
    this.logger.silly('[Identity#creditTransfer] Broadcasted IdentityCreditTransferTransition');
    return true;
}
exports.creditTransfer = creditTransfer;
exports.default = creditTransfer;
//# sourceMappingURL=creditTransfer.js.map