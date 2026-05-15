// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {Script} from "forge-std/Script.sol";
import {FacilityCovenantRegistry} from "../src/FacilityCovenantRegistry.sol";

contract DeployFacilityCovenantRegistry is Script {
    function run() external returns (FacilityCovenantRegistry registry) {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");

        vm.startBroadcast(deployerPrivateKey);
        registry = new FacilityCovenantRegistry();
        vm.stopBroadcast();
    }
}
