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

    function _buildExcludedAsset(
        string memory externalId,
        string[] memory reasons
    ) internal pure returns (FacilityCovenantRegistry.ExcludedAsset memory asset) {
        asset.externalId = externalId;
        asset.reasons = reasons;
    }

    function testDeploymentInitializesOwnerAndOpenWriteMode() public view {
        assertEq(registry.OWNER(), address(this));
        assertTrue(registry.openWrite());
    }

    function testUpdateFacilityReportAllowsAnyWriterWhileOpenWriteEnabled() public {
        string[] memory includedExternalIds = new string[](2);
        includedExternalIds[0] = "asset-001";
        includedExternalIds[1] = "asset-002";

        string[] memory exclusionReasons = new string[](2);
        exclusionReasons[0] = "ineligible flag";
        exclusionReasons[1] = "status mismatch: expected current";
        FacilityCovenantRegistry.ExcludedAsset[] memory excludedAssets =
            new FacilityCovenantRegistry.ExcludedAsset[](1);
        excludedAssets[0] = _buildExcludedAsset("asset-003", exclusionReasons);

        vm.prank(STRANGER);
        registry.updateFacilityReport(
            "educa", 527, FacilityCovenantRegistry.CovenantStatus.BREACH, 3, includedExternalIds, excludedAssets
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
        assertEq(report.excludedAssets.length, 1);
        assertEq(report.excludedAssets[0].externalId, "asset-003");
        assertEq(report.excludedAssets[0].reasons.length, 2);
        assertEq(report.excludedAssets[0].reasons[0], "ineligible flag");
        assertEq(report.excludedAssets[0].reasons[1], "status mismatch: expected current");
        assertEq(report.updatedBy, STRANGER);
        assertGt(report.updatedAt, 0);
    }

    function testRestrictedModeRejectsNonWhitelistedWriter() public {
        registry.setOpenWrite(false);

        string[] memory includedExternalIds = new string[](1);
        includedExternalIds[0] = "asset-001";
        FacilityCovenantRegistry.ExcludedAsset[] memory excludedAssets =
            new FacilityCovenantRegistry.ExcludedAsset[](0);

        vm.expectRevert(abi.encodeWithSelector(FacilityCovenantRegistry.WriterNotAllowed.selector, STRANGER));
        vm.prank(STRANGER);
        registry.updateFacilityReport(
            "payearly",
            0,
            FacilityCovenantRegistry.CovenantStatus.COMPLIANT,
            1,
            includedExternalIds,
            excludedAssets
        );
    }

    function testRestrictedModeAllowsWhitelistedWriter() public {
        registry.setOpenWrite(false);
        registry.setWriterWhitelist(WRITER, true);

        string[] memory includedExternalIds = new string[](1);
        includedExternalIds[0] = "asset-101";
        string[] memory exclusionReasons = new string[](1);
        exclusionReasons[0] = "ineligible flag";
        FacilityCovenantRegistry.ExcludedAsset[] memory excludedAssets =
            new FacilityCovenantRegistry.ExcludedAsset[](1);
        excludedAssets[0] = _buildExcludedAsset("asset-102", exclusionReasons);

        vm.prank(WRITER);
        registry.updateFacilityReport(
            "nomina",
            339,
            FacilityCovenantRegistry.CovenantStatus.COMPLIANT,
            2,
            includedExternalIds,
            excludedAssets
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
        string[] memory firstReasons = new string[](2);
        firstReasons[0] = "ineligible flag";
        firstReasons[1] = "status mismatch";
        FacilityCovenantRegistry.ExcludedAsset[] memory firstExcluded =
            new FacilityCovenantRegistry.ExcludedAsset[](1);
        firstExcluded[0] = _buildExcludedAsset("asset-c", firstReasons);

        registry.updateFacilityReport(
            "educa", 420, FacilityCovenantRegistry.CovenantStatus.COMPLIANT, 3, firstIncluded, firstExcluded
        );

        string[] memory secondIncluded = new string[](1);
        secondIncluded[0] = "asset-z";
        FacilityCovenantRegistry.ExcludedAsset[] memory secondExcluded =
            new FacilityCovenantRegistry.ExcludedAsset[](0);

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
        assertEq(report.excludedAssets.length, 0);
        assertEq(report.updatedBy, WRITER);
    }

    function testUpdateStoresMultipleExcludedAssetsWithReasons() public {
        string[] memory includedExternalIds = new string[](1);
        includedExternalIds[0] = "asset-001";

        string[] memory firstReasons = new string[](2);
        firstReasons[0] = "ineligible flag";
        firstReasons[1] = "missing interest_rate_percentage";
        string[] memory secondReasons = new string[](1);
        secondReasons[0] = "status mismatch: expected active";

        FacilityCovenantRegistry.ExcludedAsset[] memory excludedAssets =
            new FacilityCovenantRegistry.ExcludedAsset[](2);
        excludedAssets[0] = _buildExcludedAsset("asset-002", firstReasons);
        excludedAssets[1] = _buildExcludedAsset("asset-003", secondReasons);

        registry.updateFacilityReport(
            "educa", 527, FacilityCovenantRegistry.CovenantStatus.BREACH, 3, includedExternalIds, excludedAssets
        );

        FacilityCovenantRegistry.FacilityReport memory report = registry.getFacilityReport("educa");
        assertEq(report.excludedAssets.length, 2);
        assertEq(report.excludedAssets[0].externalId, "asset-002");
        assertEq(report.excludedAssets[0].reasons.length, 2);
        assertEq(report.excludedAssets[0].reasons[0], "ineligible flag");
        assertEq(report.excludedAssets[0].reasons[1], "missing interest_rate_percentage");
        assertEq(report.excludedAssets[1].externalId, "asset-003");
        assertEq(report.excludedAssets[1].reasons.length, 1);
        assertEq(report.excludedAssets[1].reasons[0], "status mismatch: expected active");
    }

    function testUpdateRevertsWhenSummaryCountsDoNotMatch() public {
        string[] memory includedExternalIds = new string[](1);
        includedExternalIds[0] = "asset-001";
        string[] memory exclusionReasons = new string[](1);
        exclusionReasons[0] = "ineligible flag";
        FacilityCovenantRegistry.ExcludedAsset[] memory excludedAssets =
            new FacilityCovenantRegistry.ExcludedAsset[](1);
        excludedAssets[0] = _buildExcludedAsset("asset-002", exclusionReasons);

        vm.expectRevert(FacilityCovenantRegistry.SummaryCountMismatch.selector);
        registry.updateFacilityReport(
            "educa", 527, FacilityCovenantRegistry.CovenantStatus.BREACH, 3, includedExternalIds, excludedAssets
        );
    }

    function testUnsupportedFacilityReverts() public {
        string[] memory includedExternalIds = new string[](0);
        FacilityCovenantRegistry.ExcludedAsset[] memory excludedAssets =
            new FacilityCovenantRegistry.ExcludedAsset[](0);

        vm.expectRevert(abi.encodeWithSelector(FacilityCovenantRegistry.UnsupportedFacility.selector, "EDUCA"));
        registry.updateFacilityReport(
            "EDUCA", 100, FacilityCovenantRegistry.CovenantStatus.COMPLIANT, 0, includedExternalIds, excludedAssets
        );
    }
}
