"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.create = void 0;
/**
 * Create and prepare contracts for the platform
 *
 * @param {Platform} this - bound instance class
 * @param contractDefinitions - contract definitions
 * @param identity - identity
 * @returns created contracts
 */
async function create(contractDefinitions, identity) {
    this.logger.debug('[Contracts#create] create data contract');
    await this.initialize();
    const identityNonce = await this.nonceManager.bumpIdentityNonce(identity.getId());
    const dataContract = this.dpp.dataContract.create(identity.getId(), BigInt(identityNonce), contractDefinitions);
    this.logger.debug(`[Contracts#create] created data contract "${dataContract.getId()}"`);
    return dataContract;
}
exports.create = create;
exports.default = create;
//# sourceMappingURL=create.js.map