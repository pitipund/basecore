import Semantic.Html 1.0

Modal{
    id: __root
	property alias textContent: _content.text
    property alias content: _content.data
    property var titleName: 'แจ้งเตือน!!!'
    property string titleColor: 'teal'
    property string buttonText: 'ตกลง'
    signal approved()

	className:'mini'
    autofocus: true

    Segments{
    	Segment{
    		className:'inverted ' + titleColor 
    		Text{
    			text: __root.titleName
    			style: 'color:white'
    		}
    	}
		Segment{
	        className: 'raised'
	        Dom{
				id: _content
                style: 'white-space: pre-wrap; line-height: 1.5;'
	        }
            Br{}
	    	Grid{
	    		Column{
	    			className:'centered five wide'
	    			Button{
                        doc_label: 'ปุ่มตกลง'
						className: titleColor + ' basic fluid'        				
	    				text: __root.buttonText
	                    onClicked:{
	                        approved()
	                    }
	                }
	            }
	    	}
		}
    }
}