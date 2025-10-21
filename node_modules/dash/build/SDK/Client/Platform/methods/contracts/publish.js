"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const broadcastStateTransition_1 = __importDefault(require("../../broadcastStateTransition"));
const signStateTransition_1 = require("../../signStateTransition");
/**
 * Publish contract onto the platform
 *
 * @param {Platform} this - bound instance class
 * @param dataContract - contract
 * @param identity - identity
 * @return {DataContractCreateTransition}
 */
async function publish(dataContract, identity) {
    this.logger.debug(`[Contracts#publish] publish data contract ${dataContract.getId()}`);
    await this.initialize();
    const { dpp } = this;
    const dataContractCreateTransition = dpp.dataContract
        .createDataContractCreateTransition(dataContract);
    this.logger.silly(`[Contracts#publish] created data contract create transition ${dataContract.getId()}`);
    await signStateTransition_1.signStateTransition(this, dataContractCreateTransition, identity, 2);
    await broadcastStateTransition_1.default(this, dataContractCreateTransition);
    // Acknowledge identifier to handle retry attempts to mitigate
    // state transition propagation lag
    this.fetcher.acknowledgeIdentifier(dataContract.getId());
    this.logger.debug(`[Contracts#publish] publish data contract ${dataContract.getId()}`);
    return dataContractCreateTransition;
}
exports.default = publish;
//# sourceMappingURL=publish.js.map