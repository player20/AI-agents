import React, { useState, useEffect } from 'react';
import './SearchBar.css';

/**
 * SearchBar component for filtering agents in the palette
 * Provides real-time search with debouncing for performance
 * Works with any search length including 1-2 characters (e.g., "PM", "QA", "iOS")
 */
const SearchBar = ({ onSearch, placeholder = 'Search agents...', debounceMs = 150 }) => {
  const [searchValue, setSearchValue] = useState('');

  // Debounced search to avoid excessive filtering on every keystroke
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      onSearch(searchValue);
    }, debounceMs);

    return () => clearTimeout(timeoutId);
  }, [searchValue, onSearch, debounceMs]);

  const handleChange = (e) => {
    setSearchValue(e.target.value);
  };

  const handleClear = () => {
    setSearchValue('');
    onSearch('');
  };

  return (
    <div className="search-bar">
      <div className="search-input-wrapper">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          className="search-input"
          placeholder={placeholder}
          value={searchValue}
          onChange={handleChange}
          aria-label="Search agents"
        />
        {searchValue && (
          <button
            className="search-clear-btn"
            onClick={handleClear}
            aria-label="Clear search"
            title="Clear search"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
};

export default SearchBar;
