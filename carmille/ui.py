"""
carmille.ui: Holds prewritten UI blocks to send to the Slack API.
"""

datetime_selection_block = [
    {
    	'type': 'section',
    	'text': {
    		'type': 'mrkdwn',
    		'text': 'Bonjour! I am happy to archive part of this channel\'s history for you.\n\n ' +
                '*Please select start and end times below (in your time zone):*'
    	}
    },
    {
    	'type': 'divider'
    },
    {
    	'type': 'section',
        'block_id': 'start-date',
    	'text': {
    		'type': 'mrkdwn',
    		'text': 'Archive Start Date:'
    	},
    	'accessory': {
    		'type': 'datepicker',
    		'initial_date': '1990-04-28',
    		'placeholder': {
    			'type': 'plain_text',
    			'text': 'Select a date',
    			'emoji': True
    		},
    		'action_id': 'start-date'
    	}
    },
    {
    	'type': 'section',
        'block_id': 'start-time',
    	'text': {
    		'type': 'mrkdwn',
    		'text': 'Archive Start Time:'
    	},
    	'accessory': {
    		'type': 'timepicker',
    		'initial_time': '13:37',
    		'placeholder': {
    			'type': 'plain_text',
    			'text': 'Select time'
    		},
    		'action_id': 'start-time'
    	}
    },
    {
    	'type': 'divider'
    },
    {
    	'type': 'section',
        'block_id': 'end-date',
    	'text': {
    		'type': 'mrkdwn',
    		'text': 'Archive End Date:'
    	},
    	'accessory': {
    		'type': 'datepicker',
    		'initial_date': '1990-04-28',
    		'placeholder': {
    			'type': 'plain_text',
    			'text': 'Select a date'
    		},
    		'action_id': 'end-date'
    	}
    },
    {
    	'type': 'section',
        'block_id': 'end-time',
    	'text': {
    		'type': 'mrkdwn',
    		'text': 'Archive End Time:'
    	},
    	'accessory': {
    		'type': 'timepicker',
    		'initial_time': '13:37',
    		'placeholder': {
    			'type': 'plain_text',
    			'text': 'Select time'
    		},
    		'action_id': 'end-time'
    	}
    },
    {
    	'type': 'divider'
    },
    {
    	'type': 'actions',
    	'elements': [
    		{
    			'type': 'button',
    			'text': {
    				'type': 'plain_text',
    				'text': 'Archive!'
    			},
    			'value': 'make_archive',
                'action_id': 'make_archive'
    		}
    	]
    },
    {
    	'type': 'divider'
    }
]
