// SPDX-License-Identifier: MIT
pragma solidity 0.8.30;

contract FacilityCovenantRegistry {
    enum CovenantStatus {
        COMPLIANT,
        BREACH
    }

    struct ExcludedAsset {
        string externalId;
        string[] reasons;
    }

    struct FacilityReport {
        string facility;
        uint16 effectiveRateBps;
        CovenantStatus covenantStatus;
        uint32 totalAssetsEvaluated;
        uint32 assetsIncludedCount;
        uint32 assetsExcludedCount;
        string[] includedExternalIds;
        ExcludedAsset[] excludedAssets;
        uint64 updatedAt;
        address updatedBy;
        bool exists;
    }

    address public immutable OWNER;
    bool public openWrite = true;

    mapping(address => bool) public whitelistedWriters;
    mapping(bytes32 => FacilityReport) private reports;
    mapping(bytes32 => bool) private supportedFacilities;

    event OpenWriteUpdated(bool indexed enabled);
    event WriterWhitelistUpdated(address indexed writer, bool indexed allowed);
    event FacilityReportUpdated(
        bytes32 indexed facilityKey,
        string facility,
        address indexed updatedBy,
        uint16 effectiveRateBps,
        CovenantStatus covenantStatus,
        uint32 totalAssetsEvaluated,
        uint32 assetsIncludedCount,
        uint32 assetsExcludedCount
    );

    error NotOwner();
    error WriterNotAllowed(address caller);
    error UnsupportedFacility(string facility);
    error EmptyFacility();
    error SummaryCountMismatch();

    constructor() {
        OWNER = msg.sender;
        _registerSupportedFacility("educa");
        _registerSupportedFacility("payearly");
        _registerSupportedFacility("nomina");
    }

    function setOpenWrite(bool enabled) external onlyOwner {
        openWrite = enabled;
        emit OpenWriteUpdated(enabled);
    }

    function setWriterWhitelist(address writer, bool allowed) external onlyOwner {
        whitelistedWriters[writer] = allowed;
        emit WriterWhitelistUpdated(writer, allowed);
    }

    function updateFacilityReport(
        string calldata facility,
        uint16 effectiveRateBps,
        CovenantStatus covenantStatus,
        uint32 totalAssetsEvaluated,
        string[] calldata includedExternalIds,
        ExcludedAsset[] calldata excludedAssets
    ) external onlyAllowedWriter {
        bytes32 reportKey = _validatedFacilityKey(facility);
        uint32 assetsIncludedCount = uint32(includedExternalIds.length);
        uint32 assetsExcludedCount = uint32(excludedAssets.length);

        if (totalAssetsEvaluated != assetsIncludedCount + assetsExcludedCount) {
            revert SummaryCountMismatch();
        }

        FacilityReport storage report = reports[reportKey];
        report.facility = facility;
        report.effectiveRateBps = effectiveRateBps;
        report.covenantStatus = covenantStatus;
        report.totalAssetsEvaluated = totalAssetsEvaluated;
        report.assetsIncludedCount = assetsIncludedCount;
        report.assetsExcludedCount = assetsExcludedCount;
        report.updatedAt = uint64(block.timestamp);
        report.updatedBy = msg.sender;
        report.exists = true;

        _replaceArray(report.includedExternalIds, includedExternalIds);
        _replaceExcludedAssets(report.excludedAssets, excludedAssets);

        emit FacilityReportUpdated(
            reportKey,
            facility,
            msg.sender,
            effectiveRateBps,
            covenantStatus,
            totalAssetsEvaluated,
            assetsIncludedCount,
            assetsExcludedCount
        );
    }

    function getFacilityReport(string calldata facility) external view returns (FacilityReport memory) {
        bytes32 reportKey = _validatedFacilityKey(facility);
        return reports[reportKey];
    }

    function reportExists(string calldata facility) external view returns (bool) {
        bytes32 reportKey = _validatedFacilityKey(facility);
        return reports[reportKey].exists;
    }

    function getFacilityKey(string calldata facility) external view returns (bytes32) {
        return _validatedFacilityKey(facility);
    }

    modifier onlyOwner() {
        _onlyOwner();
        _;
    }

    modifier onlyAllowedWriter() {
        _onlyAllowedWriter();
        _;
    }

    function _onlyOwner() internal view {
        if (msg.sender != OWNER) {
            revert NotOwner();
        }
    }

    function _onlyAllowedWriter() internal view {
        if (!openWrite && !whitelistedWriters[msg.sender]) {
            revert WriterNotAllowed(msg.sender);
        }
    }

    function _validatedFacilityKey(string calldata facility) internal view returns (bytes32 facilityKey_) {
        if (bytes(facility).length == 0) {
            revert EmptyFacility();
        }

        facilityKey_ = keccak256(bytes(facility));
        if (!supportedFacilities[facilityKey_]) {
            revert UnsupportedFacility(facility);
        }
    }

    function _registerSupportedFacility(string memory facility) internal {
        supportedFacilities[keccak256(bytes(facility))] = true;
    }

    function _replaceArray(string[] storage target, string[] calldata source) internal {
        while (target.length > 0) {
            target.pop();
        }
        for (uint256 index = 0; index < source.length; index++) {
            target.push(source[index]);
        }
    }

    function _replaceExcludedAssets(ExcludedAsset[] storage target, ExcludedAsset[] calldata source) internal {
        while (target.length > 0) {
            target.pop();
        }
        for (uint256 index = 0; index < source.length; index++) {
            target.push();
            target[index].externalId = source[index].externalId;
            _replaceArray(target[index].reasons, source[index].reasons);
        }
    }
}
