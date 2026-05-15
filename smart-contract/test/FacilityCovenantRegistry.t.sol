// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

import {Test} from "forge-std/Test.sol";
import {FacilityCovenantRegistry} from "../src/FacilityCovenantRegistry.sol";

contract FacilityCovenantRegistryTest is Test {
    FacilityCovenantRegistry internal registry;

    address internal constant WRITER = address(0xBEEF);
    address internal constant STRANGER = address(0xCAFE);

    function setUp() public {
        registry = new FacilityCovenantRegistry();
    }

    function testDeploymentInitializesOwnerAndOpenWriteMode() public view {
        assertEq(registry.OWNER(), address(this));
        assertTrue(registry.openWrite());
    }

    function testUpdateFacilityReportAllowsAnyWriterWhileOpenWriteEnabled() public {
        string[] memory includedExternalIds = new string[](2);
        includedExternalIds[0] = "asset-001";
        includedExternalIds[1] = "asset-002";

        string[] memory excludedExternalIds = new string[](1);
        excludedExternalIds[0] = "asset-003";

        vm.prank(STRANGER);
        registry.updateFacilityReport(
            "educa", 527, FacilityCovenantRegistry.CovenantStatus.BREACH, 3, includedExternalIds, excludedExternalIds
        );

        FacilityCovenantRegistry.FacilityReport memory report = registry.getFacilityReport("educa");

        assertTrue(report.exists);
        assertEq(report.facility, "educa");
        assertEq(report.effectiveRateBps, 527);
        assertEq(uint8(report.covenantStatus), uint8(FacilityCovenantRegistry.CovenantStatus.BREACH));
        assertEq(report.totalAssetsEvaluated, 3);
        assertEq(report.assetsIncludedCount, 2);
        assertEq(report.assetsExcludedCount, 1);
        assertEq(report.includedExternalIds.length, 2);
        assertEq(report.includedExternalIds[0], "asset-001");
        assertEq(report.includedExternalIds[1], "asset-002");
        assertEq(report.excludedExternalIds.length, 1);
        assertEq(report.excludedExternalIds[0], "asset-003");
        assertEq(report.updatedBy, STRANGER);
        assertGt(report.updatedAt, 0);
    }

    function testRestrictedModeRejectsNonWhitelistedWriter() public {
        registry.setOpenWrite(false);

        string[] memory includedExternalIds = new string[](1);
        includedExternalIds[0] = "asset-001";
        string[] memory excludedExternalIds = new string[](0);

        vm.expectRevert(abi.encodeWithSelector(FacilityCovenantRegistry.WriterNotAllowed.selector, STRANGER));
        vm.prank(STRANGER);
        registry.updateFacilityReport(
            "payearly",
            0,
            FacilityCovenantRegistry.CovenantStatus.COMPLIANT,
            1,
            includedExternalIds,
            excludedExternalIds
        );
    }

    function testRestrictedModeAllowsWhitelistedWriter() public {
        registry.setOpenWrite(false);
        registry.setWriterWhitelist(WRITER, true);

        string[] memory includedExternalIds = new string[](1);
        includedExternalIds[0] = "asset-101";
        string[] memory excludedExternalIds = new string[](1);
        excludedExternalIds[0] = "asset-102";

        vm.prank(WRITER);
        registry.updateFacilityReport(
            "nomina",
            339,
            FacilityCovenantRegistry.CovenantStatus.COMPLIANT,
            2,
            includedExternalIds,
            excludedExternalIds
        );

        assertTrue(registry.reportExists("nomina"));
        FacilityCovenantRegistry.FacilityReport memory report = registry.getFacilityReport("nomina");
        assertEq(report.updatedBy, WRITER);
    }

    function testReportExistsIsFalseBeforeFirstPublication() public view {
        assertFalse(registry.reportExists("educa"));
    }

    function testOverwriteReplacesStoredArraysAndMetadata() public {
        string[] memory firstIncluded = new string[](2);
        firstIncluded[0] = "asset-a";
        firstIncluded[1] = "asset-b";
        string[] memory firstExcluded = new string[](1);
        firstExcluded[0] = "asset-c";

        registry.updateFacilityReport(
            "educa", 420, FacilityCovenantRegistry.CovenantStatus.COMPLIANT, 3, firstIncluded, firstExcluded
        );

        string[] memory secondIncluded = new string[](1);
        secondIncluded[0] = "asset-z";
        string[] memory secondExcluded = new string[](0);

        vm.warp(block.timestamp + 1);
        vm.prank(WRITER);
        registry.updateFacilityReport(
            "educa", 500, FacilityCovenantRegistry.CovenantStatus.BREACH, 1, secondIncluded, secondExcluded
        );

        FacilityCovenantRegistry.FacilityReport memory report = registry.getFacilityReport("educa");

        assertEq(report.effectiveRateBps, 500);
        assertEq(uint8(report.covenantStatus), uint8(FacilityCovenantRegistry.CovenantStatus.BREACH));
        assertEq(report.totalAssetsEvaluated, 1);
        assertEq(report.assetsIncludedCount, 1);
        assertEq(report.assetsExcludedCount, 0);
        assertEq(report.includedExternalIds.length, 1);
        assertEq(report.includedExternalIds[0], "asset-z");
        assertEq(report.excludedExternalIds.length, 0);
        assertEq(report.updatedBy, WRITER);
    }

    function testUpdateRevertsWhenSummaryCountsDoNotMatch() public {
        string[] memory includedExternalIds = new string[](1);
        includedExternalIds[0] = "asset-001";
        string[] memory excludedExternalIds = new string[](1);
        excludedExternalIds[0] = "asset-002";

        vm.expectRevert(FacilityCovenantRegistry.SummaryCountMismatch.selector);
        registry.updateFacilityReport(
            "educa", 527, FacilityCovenantRegistry.CovenantStatus.BREACH, 3, includedExternalIds, excludedExternalIds
        );
    }

    function testUnsupportedFacilityReverts() public {
        string[] memory includedExternalIds = new string[](0);
        string[] memory excludedExternalIds = new string[](0);

        vm.expectRevert(abi.encodeWithSelector(FacilityCovenantRegistry.UnsupportedFacility.selector, "EDUCA"));
        registry.updateFacilityReport(
            "EDUCA", 100, FacilityCovenantRegistry.CovenantStatus.COMPLIANT, 0, includedExternalIds, excludedExternalIds
        );
    }
}
