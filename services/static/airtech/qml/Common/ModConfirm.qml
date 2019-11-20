import Semantic.Html 1.0

Modal{
    id: root
    property alias textContent: _content.text
    property alias content: _content.data
    property var titleName: 'แจ้งเตือน!!!'
    property var size: 'mini'
    property string titleColor: 'blue'
	property string approveButtonText: 'ใช่'
	property string denyButtonText: 'ไม่'
	property string approveButtonColor: 'green'
	property string denyButtonColor: 'red'
    signal approve()
    signal deny()

	className: size
    autofocus: true

    function ask(approveCallback, denyCallback) {
        root.approveCallback = approveCallback || function(){}
        root.denyCallback = denyCallback || function(){}
        root.show()
    }

    Segments{
    	Segment{
    		className:'inverted ' + titleColor
			text: root.titleName
    	}
		Segment{
	        className: 'raised'
	        Dom{
				id: _content
	        }
            Br{}
	    	Grid{
	    		Column{
	    			className:'centered five wide'
	    			Button{
						basic: true
						fluid: true
	    				text: approveButtonText
						backgroundColor: approveButtonColor
	                    onClicked:{
                            root.approveCallback && root.approveCallback()
                            root.approve()
							root.approveCallback = function(){}
	                    }
	                }

	            }
	    		Column{
	    			className:'centered five wide'
	    			Button{
						basic: true
						fluid: true
	    				text: denyButtonText
						backgroundColor: denyButtonColor
	                    onClicked:{
                            root.denyCallback && root.denyCallback()
                            root.deny()
                            root.denyCallback = function(){}
	                    }
	                }
	            }
	    	}
		}
    }
}