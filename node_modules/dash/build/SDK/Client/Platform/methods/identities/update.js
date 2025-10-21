"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.update = void 0;
const signStateTransition_1 = require("../../signStateTransition");
const broadcastStateTransition_1 = __importDefault(require("../../broadcastStateTransition"));
/**
 * Update platform identities
 *
 * @param {Platform} this - bound instance class
 * @param {Identity} identity - identity to update
 * @param {{add: IdentityPublicKey[]; disable: IdentityPublicKey[]}} publicKeys - public keys to add
 * @param {Object<string, any>} privateKeys - public keys to add
 *
 * @returns {boolean}
 */
async function update(identity, publicKeys, privateKeys) {
    this.logger.debug(`[Identity#update] Update identity ${identity.getId().toString()}`, {
        addKeys: publicKeys.add ? publicKeys.add.length : 0,
        disableKeys: publicKeys.disable ? publicKeys.disable.map((key) => key.getId()).join(', ') : 'none',
    });
    await this.initialize();
    const { dpp } = this;
    const identityNonce = await this.nonceManager.bumpIdentityNonce(identity.getId());
    const identityUpdateTransition = dpp.identity.createIdentityUpdateTransition(identity, BigInt(identityNonce), publicKeys);
    this.logger.silly('[Identity#update] Created IdentityUpdateTransition');
    const signerKeyIndex = 0;
    // Create key proofs
    if (identityUpdateTransition.getPublicKeysToAdd()) {
        const signerKey = identity.getPublicKeys()[signerKeyIndex];
        // must be run sequentially! will not work with Promise.all!
        // more info at https://jrsinclair.com/articles/2019/how-to-run-async-js-in-parallel-or-sequential/
        const starterPromise = Promise.resolve(null);
        const updatedPublicKeys = [];
        await identityUpdateTransition.getPublicKeysToAdd().reduce((previousPromise, publicKey) => previousPromise.then(async () => {
            const privateKey = privateKeys[publicKey.getId()];
            if (!privateKey) {
                throw new Error(`Private key for key ${publicKey.getId()} not found`);
            }
            identityUpdateTransition.setSignaturePublicKeyId(signerKey.getId());
            await identityUpdateTransition.signByPrivateKey(privateKey.toBuffer(), publicKey.getType());
            publicKey.setSignature(identityUpdateTransition.getSignature());
            updatedPublicKeys.push(publicKey);
            identityUpdateTransition.setSignature(undefined);
            identityUpdateTransition.setSignaturePublicKeyId(undefined);
        }), starterPromise);
        // Update public keys in transition to include signatures
        identityUpdateTransition.setPublicKeysToAdd(updatedPublicKeys);
    }
    await signStateTransition_1.signStateTransition(this, identityUpdateTransition, identity, signerKeyIndex);
    this.logger.silly('[Identity#update] Signed IdentityUpdateTransition');
    // TODO(versioning): restore
    // @ts-ignore
    // const result = await dpp.stateTransition.validateBasic(
    //   identityUpdateTransition,
    //   // TODO(v0.24-backport): get rid of this once decided
    //   //  whether we need execution context in wasm bindings
    //   new StateTransitionExecutionContext(),
    // );
    // if (!result.isValid()) {
    //   const messages = result.getErrors().map((error) => error.message);
    //   throw new Error(`StateTransition is invalid - ${JSON.stringify(messages)}`);
    // }
    this.logger.silly('[Identity#update] Validated IdentityUpdateTransition');
    // Skipping validation because it's already done above
    await broadcastStateTransition_1.default(this, identityUpdateTransition, {
        skipValidation: true,
    });
    this.logger.silly('[Identity#update] Broadcasted IdentityUpdateTransition');
    return true;
}
exports.update = update;
exports.default = update;
//# sourceMappingURL=update.js.map