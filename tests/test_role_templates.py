"""Tests for role templates functionality"""

import pytest
from src.models.role_templates import (
    get_role_template,
    list_role_templates,
    get_all_role_templates,
    get_role_template_info,
    ROLE_TEMPLATES
)
from src.models import Role


def test_list_role_templates():
    """Test listing all available role templates"""
    templates = list_role_templates()
    
    assert isinstance(templates, list)
    assert len(templates) > 0
    
    # Check that expected templates are present
    expected_templates = [
        'product_manager',
        'software_engineer',
        'ux_designer',
        'qa_engineer',
        'data_analyst',
        'business_analyst',
        'devops_engineer',
        'security_engineer',
        'technical_writer',
        'project_manager'
    ]
    
    for template in expected_templates:
        assert template in templates


def test_get_role_template():
    """Test getting a specific role template"""
    role = get_role_template('product_manager')
    
    assert isinstance(role, Role)
    assert role.name == "Product Manager"
    assert len(role.description) > 0
    assert len(role.system_prompt) > 0
    assert "product" in role.description.lower() or "product" in role.system_prompt.lower()


def test_get_role_template_returns_copy():
    """Test that get_role_template returns a copy, not the original"""
    role1 = get_role_template('software_engineer')
    role2 = get_role_template('software_engineer')
    
    # They should be equal but not the same object
    assert role1.name == role2.name
    assert role1.description == role2.description
    assert role1.system_prompt == role2.system_prompt
    assert role1 is not role2


def test_get_role_template_invalid_name():
    """Test that getting an invalid template raises KeyError"""
    with pytest.raises(KeyError) as exc_info:
        get_role_template('invalid_template_name')
    
    assert 'invalid_template_name' in str(exc_info.value)
    assert 'not found' in str(exc_info.value).lower()


def test_get_all_role_templates():
    """Test getting all role templates"""
    all_templates = get_all_role_templates()
    
    assert isinstance(all_templates, dict)
    assert len(all_templates) > 0
    
    # Check that all templates are Role objects
    for name, role in all_templates.items():
        assert isinstance(role, Role)
        assert len(role.name) > 0
        assert len(role.description) > 0
        assert len(role.system_prompt) > 0


def test_get_all_role_templates_returns_copies():
    """Test that get_all_role_templates returns copies"""
    all_templates1 = get_all_role_templates()
    all_templates2 = get_all_role_templates()
    
    # Check that we get different objects
    for name in all_templates1.keys():
        assert all_templates1[name] is not all_templates2[name]
        assert all_templates1[name].name == all_templates2[name].name


def test_get_role_template_info():
    """Test getting role template info"""
    info = get_role_template_info('ux_designer')
    
    assert isinstance(info, dict)
    assert 'name' in info
    assert 'description' in info
    assert info['name'] == "UX Designer"
    assert len(info['description']) > 0


def test_get_role_template_info_invalid_name():
    """Test that getting info for invalid template raises KeyError"""
    with pytest.raises(KeyError) as exc_info:
        get_role_template_info('nonexistent_role')
    
    assert 'nonexistent_role' in str(exc_info.value)


def test_all_templates_have_required_fields():
    """Test that all templates have valid required fields"""
    for template_name in list_role_templates():
        role = get_role_template(template_name)
        
        # Check that all required fields are present and non-empty
        assert role.name and role.name.strip(), f"Template {template_name} has empty name"
        assert role.description and role.description.strip(), f"Template {template_name} has empty description"
        assert role.system_prompt and role.system_prompt.strip(), f"Template {template_name} has empty system_prompt"
        
        # Check length constraints
        assert len(role.name) <= 50, f"Template {template_name} name too long"
        assert 1 <= len(role.description) <= 2000, f"Template {template_name} description length invalid"
        assert len(role.system_prompt) <= 2000, f"Template {template_name} system_prompt too long"


def test_template_roles_are_valid():
    """Test that all template roles pass validation"""
    for template_name in list_role_templates():
        role = get_role_template(template_name)
        
        # This should not raise any validation errors
        role.validate()


def test_specific_templates_content():
    """Test specific templates have appropriate content"""
    # Product Manager
    pm = get_role_template('product_manager')
    assert 'product' in pm.system_prompt.lower()
    assert 'user' in pm.system_prompt.lower() or 'customer' in pm.system_prompt.lower()
    
    # Software Engineer
    engineer = get_role_template('software_engineer')
    assert 'code' in engineer.system_prompt.lower() or 'technical' in engineer.system_prompt.lower()
    
    # UX Designer
    designer = get_role_template('ux_designer')
    assert 'user' in designer.system_prompt.lower() or 'design' in designer.system_prompt.lower()
    
    # QA Engineer
    qa = get_role_template('qa_engineer')
    assert 'test' in qa.system_prompt.lower() or 'quality' in qa.system_prompt.lower()
    
    # Security Engineer
    security = get_role_template('security_engineer')
    assert 'security' in security.system_prompt.lower()


def test_role_templates_constant_not_modified():
    """Test that the ROLE_TEMPLATES constant is not accidentally modified"""
    original_count = len(ROLE_TEMPLATES)
    original_pm_name = ROLE_TEMPLATES['product_manager'].name
    
    # Get a template and try to modify it
    role = get_role_template('product_manager')
    
    # Verify we still have the same number of templates
    assert len(ROLE_TEMPLATES) == original_count
    assert ROLE_TEMPLATES['product_manager'].name == original_pm_name
