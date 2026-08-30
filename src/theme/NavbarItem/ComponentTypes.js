import ComponentTypes from '@theme-original/NavbarItem/ComponentTypes';
import DocumentationDropdownNavbarItem from '@site/src/components/DocumentationDropdownNavbarItem';
import LanguageSwitcherNavbarItem from '@site/src/components/LanguageSwitcherNavbarItem';
import LocaleAwareNavbarItem from '@site/src/components/LocaleAwareNavbarItem';

export default {
  ...ComponentTypes,
  'custom-documentationDropdown': DocumentationDropdownNavbarItem,
  'custom-languageSwitcher': LanguageSwitcherNavbarItem,
  'custom-localeAwareLink': LocaleAwareNavbarItem,
};
