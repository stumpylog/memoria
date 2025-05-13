import React from 'react';
import { Container, Row, Col } from 'react-bootstrap';
import ImageCard from './ImageCard';
import type { ImageThumbnailSchema } from '../../api';

interface ImageWallProps {
    images: ImageThumbnailSchema[];
    showViewButton?: boolean;
    onImageClick?: (id: number) => void;
    columns?: number;
}

const ImageWall: React.FC<ImageWallProps> = ({
    images,
    showViewButton = true,
    onImageClick,
    columns = 3
}) => {
    // Calculate column width based on the number of columns
    const getColumnClass = () => {
        switch (columns) {
            case 1: return "col-12";
            case 2: return "col-md-6";
            case 3: return "col-md-4";
            case 4: return "col-lg-3 col-md-4 col-sm-6";
            case 6: return "col-lg-2 col-md-4 col-sm-6";
            default: return "col-md-4";
        }
    };

    return (
        <Container>
            <Row>
                {images.map(image => (
                    <Col key={image.id} className={`${getColumnClass()} mb-4`}>
                        <ImageCard
                            image={image}
                            showViewButton={showViewButton}
                            onViewClick={onImageClick}
                        />
                    </Col>
                ))}
            </Row>
        </Container>
    );
};

export default ImageWall;
