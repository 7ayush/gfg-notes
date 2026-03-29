# Requirements Document

## Introduction

A robust, recursive web scraper for GeeksforGeeks (GfG) study material. The scraper accepts a starting URL, extracts the core article content, follows internal GfG article links found within that content up to a configurable depth, and saves everything into a neatly organized, nested local file system as Markdown (.md) files. The scraper must be polite, resilient to errors, and produce clean, interlinked local Markdown output.

## Glossary

- **Scraper**: The Python web scraping application that fetches, parses, and saves GfG articles.
- **Article_Content**: The main body of a GeeksforGeeks article page, excluding sidebars, navigation menus, headers, footers, comment sections, pop-ups, and ads. Typically found within the `<article>` tag or main content `<div>`.
- **Internal_Link**: A hyperlink whose domain is `geeksforgeeks.org`, found within the Article_Content.
- **Visited_Set**: An in-memory set of URLs that have already been fetched or are queued for fetching, used to prevent duplicate processing and infinite loops.
- **MAX_DEPTH**: A configurable integer parameter that limits how many levels of recursive link-following the Scraper performs from the starting URL.
- **Markdown_File**: A `.md` file containing the converted article content in clean, readable Markdown format.
- **Output_Directory**: The root local directory where all scraped Markdown_Files and subdirectories are saved.
- **Discovery_Order**: The sequential position (1-based) in which an Internal_Link is encountered on a parent page's Article_Content, used for filename numbering.
- **Polite_Delay**: A configurable pause (in seconds) between consecutive HTTP requests to avoid overwhelming the target server.
- **User_Agent**: A standard web browser User-Agent string sent in HTTP request headers to identify the Scraper as a regular browser.
- **Markdown_Converter**: A library (such as `markdownify` or `html2text`) used to convert extracted HTML into Markdown format.

## Requirements

### Requirement 1: Core Content Extraction

**User Story:** As a user, I want the scraper to extract only the main article body from a GfG page, so that I get clean study material without clutter.

#### Acceptance Criteria

1. WHEN a GfG page is fetched, THE Scraper SHALL identify the Article_Content by targeting the `<article>` tag or the main content `<div>` in the page DOM.
2. THE Scraper SHALL strip all sidebars, navigation menus, headers, footers, comment sections, pop-ups, and advertisement elements from the extracted content.
3. IF the expected Article_Content structure is not found on a page, THEN THE Scraper SHALL log a warning message identifying the URL and continue processing remaining URLs without crashing.

### Requirement 2: Markdown Conversion

**User Story:** As a user, I want the extracted HTML content converted into clean Markdown files, so that I can read and navigate the material offline in any Markdown viewer.

#### Acceptance Criteria

1. THE Scraper SHALL convert extracted Article_Content HTML into clean, readable Markdown format using a dedicated Markdown_Converter library.
2. THE Scraper SHALL save each converted article as a Markdown_File with the `.md` extension.
3. THE Scraper SHALL preserve the semantic structure of the original article (headings, code blocks, lists, tables, bold/italic text, and images) during Markdown conversion.

### Requirement 3: Recursive Link Discovery

**User Story:** As a user, I want the scraper to follow internal GfG links found within article content, so that I can download an entire tutorial path automatically.

#### Acceptance Criteria

1. THE Scraper SHALL extract hyperlinks only from within the Article_Content, not from sidebars, navigation, footers, or other page elements.
2. THE Scraper SHALL follow only Internal_Links whose domain is `geeksforgeeks.org`.
3. THE Scraper SHALL ignore external links, anchor-only links, and non-HTTP(S) links found within the Article_Content.
4. WHEN an Internal_Link is discovered, THE Scraper SHALL normalize the URL by removing query parameters and fragments before adding it to the processing queue.

### Requirement 4: Depth Limiting

**User Story:** As a user, I want to configure a maximum recursion depth, so that the scraper does not endlessly follow cross-links across the entire GfG site.

#### Acceptance Criteria

1. THE Scraper SHALL accept a configurable MAX_DEPTH parameter that limits the number of recursive levels from the starting URL.
2. THE Scraper SHALL default MAX_DEPTH to 2 when no value is provided by the user.
3. WHILE the current recursion depth equals MAX_DEPTH, THE Scraper SHALL save the current page content but SHALL NOT follow any Internal_Links found on that page.
4. THE Scraper SHALL treat the starting URL as depth 0.

### Requirement 5: Cycle Prevention

**User Story:** As a user, I want the scraper to avoid re-downloading pages it has already visited, so that it does not enter infinite loops or waste time on duplicates.

#### Acceptance Criteria

1. THE Scraper SHALL maintain a Visited_Set containing all URLs that have been fetched or are queued for fetching.
2. WHEN an Internal_Link is discovered that already exists in the Visited_Set, THE Scraper SHALL skip fetching that URL.
3. THE Scraper SHALL add each URL to the Visited_Set before initiating the HTTP request for that URL.

### Requirement 6: Local Link Rewriting

**User Story:** As a user, I want hyperlinks in the downloaded Markdown to point to local files instead of live URLs, so that I can navigate between articles offline.

#### Acceptance Criteria

1. WHEN an Internal_Link in the Article_Content corresponds to a page that has been scraped, THE Scraper SHALL rewrite that hyperlink in the Markdown_File to use a relative file path pointing to the local Markdown_File.
2. WHEN an Internal_Link in the Article_Content corresponds to a page that has NOT been scraped (e.g., beyond MAX_DEPTH or excluded), THE Scraper SHALL retain the original absolute URL in the Markdown_File.

### Requirement 7: File System Organization

**User Story:** As a user, I want the scraped files organized in a nested directory structure with numbered filenames, so that I can browse the material in the correct reading order.

#### Acceptance Criteria

1. THE Scraper SHALL create a nested directory structure within the Output_Directory that mirrors the hierarchy of the tutorial path being scraped.
2. THE Scraper SHALL prepend a zero-padded Discovery_Order number to each filename (e.g., `01_Introduction.md`, `02_Data_Types.md`).
3. THE Scraper SHALL derive filenames from the URL path slug, replacing hyphens and special characters with underscores.
4. THE Scraper SHALL create parent directories automatically if they do not already exist.

### Requirement 8: Polite Request Behavior

**User Story:** As a user, I want the scraper to behave politely toward the GfG server, so that my IP is not blocked and the server is not overwhelmed.

#### Acceptance Criteria

1. THE Scraper SHALL include a User_Agent header in every HTTP request that mimics a standard web browser (e.g., a recent Chrome or Firefox User-Agent string).
2. THE Scraper SHALL NOT use the default Python `requests` library User-Agent header.
3. THE Scraper SHALL pause for a configurable Polite_Delay (defaulting to 2 seconds) between consecutive HTTP requests.

### Requirement 9: Error Handling and Resilience

**User Story:** As a user, I want the scraper to handle errors gracefully, so that a single broken link or timeout does not crash the entire scraping session.

#### Acceptance Criteria

1. IF an HTTP request fails due to a network error or timeout, THEN THE Scraper SHALL log the error with the URL and the error message, and continue processing remaining URLs.
2. IF an HTTP response returns a non-2xx status code, THEN THE Scraper SHALL log the status code and URL, and skip that page without crashing.
3. IF an unexpected error occurs during HTML parsing or Markdown conversion, THEN THE Scraper SHALL log the error with the URL and continue processing remaining URLs.
4. THE Scraper SHALL set a configurable HTTP request timeout (defaulting to 30 seconds) for each request.

### Requirement 10: Command-Line Interface and Configuration

**User Story:** As a user, I want to run the scraper from the command line with clear parameters, so that I can easily configure the starting URL, depth, and output location.

#### Acceptance Criteria

1. THE Scraper SHALL accept the starting URL as a required command-line argument.
2. THE Scraper SHALL accept optional command-line arguments for MAX_DEPTH, Output_Directory, and Polite_Delay.
3. THE Scraper SHALL print a summary upon completion showing the total number of pages scraped and the Output_Directory path.
4. THE Scraper SHALL print progress messages to the console as each page is fetched and saved.
