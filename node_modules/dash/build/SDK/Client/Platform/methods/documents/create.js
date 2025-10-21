"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.create = void 0;
/**
 * Create and prepare documents for the platform
 *
 * @param {Platform} this - bound instance class
 * @param {string} typeLocator - type locator
 * @param identity - identity
 * @param {Object} [data] - options
 */
async function create(typeLocator, identity, data = {}) {
    this.logger.debug(`[Document#create] Create document "${typeLocator}"`);
    await this.initialize();
    const { dpp } = this;
    const appNames = this.client.getApps().getNames();
    // We can either provide of type `dashpay.profile`
    // or if only one schema provided, of type `profile`.
    const [appName, fieldType] = (typeLocator.includes('.')) ? typeLocator.split('.') : [appNames[0], typeLocator];
    const { contractId } = this.client.getApps().get(appName);
    const dataContract = await this.contracts.get(contractId);
    this.logger.silly(`[Document#create] Obtained data contract ${dataContract.getId()}`);
    if (dataContract === null) {
        throw new Error(`Contract ${appName} not found. Ensure contractId ${contractId} is correct.`);
    }
    const document = dpp.document.create(dataContract, identity.getId(), fieldType, data);
    this.logger.debug(`[Document#create] Created document ${typeLocator} for data contract ${dataContract.getId()}}`);
    return document;
}
exports.create = create;
exports.default = create;
//# sourceMappingURL=create.js.map