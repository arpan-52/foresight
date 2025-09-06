#!/usr/bin/env python3
"""
Basic tests for foresight package.
"""

import numpy as np
import pytest
from foresight.core import parse_source_types, deg_to_hms_dms

def test_parse_source_types():
    """Test source type parsing."""
    # Test basic types
    assert parse_source_types("S") == ['S']
    assert parse_source_types("S,M") == ['S', 'M']
    assert parse_source_types("single,multiple") == ['S', 'M']
    
    # Test case insensitive
    assert parse_source_types("s,m") == ['S', 'M']
    
    # Test duplicates removal
    assert parse_source_types("S,S,M") == ['S', 'M']
    
    # Test invalid type
    result = parse_source_types("X")
    assert result == ['S']  # Should default to S

def test_coordinate_conversion():
    """Test coordinate conversion."""
    # Test known coordinates
    ra_deg = 187.5  # 12:30:00
    dec_deg = 45.0  # +45:00:00
    
    ra_str, dec_str = deg_to_hms_dms(ra_deg, dec_deg)
    
    assert ra_str == "12:30:00.000"
    assert dec_str == "+45.00.00.000"
    
    # Test negative declination
    ra_deg = 0.0
    dec_deg = -30.0
    
    ra_str, dec_str = deg_to_hms_dms(ra_deg, dec_deg)
    
    assert ra_str == "00:00:00.000"
    assert dec_str == "-30.00.00.000"

if __name__ == "__main__":
    pytest.main([__file__])
