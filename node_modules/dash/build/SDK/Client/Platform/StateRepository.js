"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
class StateRepository {
    constructor(client) {
        this.client = client;
    }
    async fetchIdentity(id) {
        return this.client.platform.identities.get(id);
    }
    async fetchDataContract(identifier) {
        return this.client.platform.contracts.get(identifier);
    }
    // eslint-disable-next-line
    async isAssetLockTransactionOutPointAlreadyUsed() {
        // This check still exists on the client side, however there's no need to
        // perform the check as in this client we always use a new transaction
        // register/top up identity
        return false;
    }
    // eslint-disable-next-line
    async verifyInstantLock() {
        // verification will be implemented later with DAPI SPV functionality
        return true;
    }
    async fetchTransaction(id) {
        const walletAccount = await this.client.getWalletAccount();
        // @ts-ignore
        const { transaction } = await walletAccount.getTransaction(id);
        return {
            data: transaction.toBuffer(),
            // we don't have transaction heights atm
            // and it will be implemented later with DAPI SPV functionality
            height: 1,
        };
    }
    async fetchLatestPlatformCoreChainLockedHeight() {
        return this.client.wallet.transport.getBestBlockHeight();
    }
}
exports.default = StateRepository;
//# sourceMappingURL=StateRepository.js.map