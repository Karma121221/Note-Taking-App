import React from 'react';
import {
  Box,
  Typography,
  Checkbox,
  FormControlLabel,
  Stack
} from '@mui/material';

const InteractiveContent = ({ content, onContentChange, readOnly = false, maxLines = null }) => {
  const parseContentWithCheckboxes = (text) => {
    if (!text) return [];
    
    const lines = text.split('\n');
    const elements = [];
    
    lines.forEach((line, index) => {
      // Check if line contains a checkbox pattern: - [ ] or - [x]
      const checkboxMatch = line.match(/^(\s*)-\s*\[([ x])\]\s*(.*)$/);
      
      if (checkboxMatch) {
        const [, indent, checkState, taskText] = checkboxMatch;
        const isChecked = checkState.toLowerCase() === 'x';
        const indentLevel = indent.length;
        
        elements.push({
          type: 'checkbox',
          id: `checkbox-${index}`,
          lineIndex: index,
          checked: isChecked,
          text: taskText.trim(),
          indent: indentLevel,
          originalLine: line
        });
      } else if (line.trim() !== '') {
        // Regular text line
        elements.push({
          type: 'text',
          id: `text-${index}`,
          lineIndex: index,
          text: line,
          originalLine: line
        });
      } else {
        // Empty line
        elements.push({
          type: 'empty',
          id: `empty-${index}`,
          lineIndex: index,
          originalLine: line
        });
      }
    });
    
    return elements;
  };

  const handleCheckboxToggle = (lineIndex, currentChecked) => {
    if (readOnly || !onContentChange) return;
    
    const lines = content.split('\n');
    const line = lines[lineIndex];
    
    // Toggle the checkbox state
    const newState = currentChecked ? ' ' : 'x';
    const newLine = line.replace(/^(\s*-\s*\[)[ x](\]\s*.*)$/, `$1${newState}$2`);
    
    lines[lineIndex] = newLine;
    const newContent = lines.join('\n');
    
    onContentChange(newContent);
  };

  const formatTextWithMarkdown = (text) => {
    // Simple markdown formatting
    let formatted = text;
    
    // Bold text: **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic text: *text*
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    return formatted;
  };

  const elements = parseContentWithCheckboxes(content);
  
  // Limit elements if maxLines is specified (for previews)
  const displayElements = maxLines ? elements.slice(0, maxLines) : elements;
  const hasMore = maxLines && elements.length > maxLines;

  return (
    <Box sx={{ width: '100%' }}>
      <Stack spacing={0.5}>
        {displayElements.map((element) => {
          switch (element.type) {
            case 'checkbox':
              return (
                <Box
                  key={element.id}
                  sx={{
                    ml: element.indent * 2,
                    display: 'flex',
                    alignItems: 'flex-start'
                  }}
                >
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={element.checked}
                        onChange={() => handleCheckboxToggle(element.lineIndex, element.checked)}
                        size="small"
                        disabled={readOnly}
                        sx={{
                          py: 0.5,
                          '&.Mui-checked': {
                            color: 'success.main'
                          }
                        }}
                      />
                    }
                    label={
                      <Typography
                        variant="body2"
                        sx={{
                          textDecoration: element.checked ? 'line-through' : 'none',
                          opacity: element.checked ? 0.7 : 1,
                          color: element.checked ? 'text.secondary' : 'text.primary'
                        }}
                        dangerouslySetInnerHTML={{
                          __html: formatTextWithMarkdown(element.text)
                        }}
                      />
                    }
                    sx={{
                      ml: 0,
                      mr: 0,
                      alignItems: 'flex-start',
                      '& .MuiFormControlLabel-label': {
                        paddingTop: '2px'
                      }
                    }}
                  />
                </Box>
              );
              
            case 'text':
              return (
                <Typography
                  key={element.id}
                  variant="body2"
                  sx={{
                    whiteSpace: 'pre-wrap',
                    lineHeight: 1.6
                  }}
                  dangerouslySetInnerHTML={{
                    __html: formatTextWithMarkdown(element.text)
                  }}
                />
              );
              
            case 'empty':
              return (
                <Box key={element.id} sx={{ height: 8 }} />
              );
              
            default:
              return null;
          }
        })}
        
        {hasMore && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontStyle: 'italic', textAlign: 'center', py: 1 }}
          >
            ... and {elements.length - maxLines} more lines
          </Typography>
        )}
      </Stack>
    </Box>
  );
};

export default InteractiveContent;