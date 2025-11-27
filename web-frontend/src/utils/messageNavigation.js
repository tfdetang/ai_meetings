/**
 * Message Navigation Utilities
 * Helper functions for scrolling to and highlighting messages
 */

/**
 * Scroll to a specific message in the message list
 * @param {string} messageId - The ID of the message to scroll to
 * @param {Object} options - Scroll options
 * @param {boolean} options.smooth - Whether to use smooth scrolling
 * @param {boolean} options.highlight - Whether to highlight the message
 * @param {number} options.highlightDuration - Duration to keep highlight (ms)
 */
export function scrollToMessage(messageId, options = {}) {
  const {
    smooth = true,
    highlight = true,
    highlightDuration = 3000
  } = options;

  // Find the message element
  const messageElement = document.getElementById(`message-${messageId}`);
  
  if (!messageElement) {
    console.warn(`Message element not found: ${messageId}`);
    return false;
  }

  // Scroll to the message
  messageElement.scrollIntoView({
    behavior: smooth ? 'smooth' : 'auto',
    block: 'center',
    inline: 'nearest'
  });

  // Highlight the message
  if (highlight) {
    highlightMessage(messageElement, highlightDuration);
  }

  return true;
}

/**
 * Highlight a message element temporarily
 * @param {HTMLElement} element - The message element to highlight
 * @param {number} duration - Duration to keep highlight (ms)
 */
export function highlightMessage(element, duration = 3000) {
  if (!element) return;

  // Store original styles
  const originalBackground = element.style.backgroundColor;
  const originalTransition = element.style.transition;

  // Apply highlight
  element.style.transition = 'background-color 0.3s ease';
  element.style.backgroundColor = '#fff7e6'; // Light orange highlight

  // Remove highlight after duration
  setTimeout(() => {
    element.style.backgroundColor = originalBackground;
    
    // Restore original transition after animation
    setTimeout(() => {
      element.style.transition = originalTransition;
    }, 300);
  }, duration);
}

/**
 * Get the position of a message in the list
 * @param {string} messageId - The ID of the message
 * @param {Array} messages - Array of all messages
 * @returns {number} - The index of the message, or -1 if not found
 */
export function getMessagePosition(messageId, messages) {
  return messages.findIndex(msg => msg.id === messageId);
}

/**
 * Check if a message element is currently visible in the viewport
 * @param {string} messageId - The ID of the message
 * @returns {boolean} - Whether the message is visible
 */
export function isMessageVisible(messageId) {
  const messageElement = document.getElementById(`message-${messageId}`);
  
  if (!messageElement) {
    return false;
  }

  const rect = messageElement.getBoundingClientRect();
  const windowHeight = window.innerHeight || document.documentElement.clientHeight;
  const windowWidth = window.innerWidth || document.documentElement.clientWidth;

  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= windowHeight &&
    rect.right <= windowWidth
  );
}

/**
 * Navigate to a message and return navigation info
 * @param {string} messageId - The ID of the message to navigate to
 * @param {Array} messages - Array of all messages
 * @param {Object} options - Navigation options
 * @returns {Object} - Navigation result with success status and message info
 */
export function navigateToMessage(messageId, messages, options = {}) {
  const position = getMessagePosition(messageId, messages);
  
  if (position === -1) {
    return {
      success: false,
      error: 'Message not found',
      messageId
    };
  }

  const scrolled = scrollToMessage(messageId, options);
  
  return {
    success: scrolled,
    messageId,
    position,
    message: messages[position],
    wasVisible: isMessageVisible(messageId)
  };
}
