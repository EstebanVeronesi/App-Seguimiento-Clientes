"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.topUp = void 0;
const wasm_dpp_1 = require("@dashevo/wasm-dpp");
const broadcastStateTransition_1 = __importDefault(require("../../broadcastStateTransition"));
/**
 * Register identities to the platform
 *
 * @param {Platform} this - bound instance class
 * @param {Identifier|string} identityId - id of the identity to top up
 * @param {number} amount - amount to top up in duffs
 * @returns {boolean}
 */
async function topUp(identityId, amount) {
    this.logger.debug(`[Identity#topUp] Top up identity ${identityId.toString()} with amount ${amount}`);
    await this.initialize();
    const { client } = this;
    identityId = wasm_dpp_1.Identifier.from(identityId);
    const account = await client.getWalletAccount();
    const { transaction: assetLockTransaction, privateKey: assetLockPrivateKey, outputIndex: assetLockOutputIndex, } = await this.identities.utils.createAssetLockTransaction(amount);
    // Broadcast Asset Lock transaction
    await account.broadcastTransaction(assetLockTransaction);
    this.logger.silly(`[Identity#topUp] Broadcasted asset lock transaction "${assetLockTransaction.hash}"`);
    // Create a proof for the asset lock transaction
    const assetLockProof = await this.identities.utils
        .createAssetLockProof(assetLockTransaction, assetLockOutputIndex);
    this.logger.silly(`[Identity#topUp] Created asset lock proof with tx "${assetLockTransaction.hash}"`);
    const identityTopUpTransition = await this.identities.utils
        .createIdentityTopUpTransition(assetLockProof, assetLockPrivateKey, identityId);
    this.logger.silly(`[Identity#topUp] Created IdentityTopUpTransition with asset lock tx "${assetLockTransaction.hash}"`);
    // Skipping validation because it's already done in createIdentityTopUpTransition
    await broadcastStateTransition_1.default(this, identityTopUpTransition, {
        skipValidation: true,
    });
    this.logger.silly('[Identity#topUp] Broadcasted IdentityTopUpTransition');
    return true;
}
exports.topUp = topUp;
exports.default = topUp;
//# sourceMappingURL=topUp.js.map