import React from 'react';
import { Card, Button } from 'react-bootstrap';
import type { ImageThumbnailSchema } from '../../api';

interface ImageCardProps {
    image: ImageThumbnailSchema;
    showViewButton?: boolean;
    onViewClick?: (id: number) => void;
}

const ImageCard: React.FC<ImageCardProps> = ({
    image,
    showViewButton = true,
    onViewClick
}) => {
    const handleViewClick = () => {
        if (onViewClick) {
            onViewClick(image.id);
        }
    };

    return (
        <Card className="h-100">
            <div
                style={{
                    height: '200px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    overflow: 'hidden',
                    backgroundColor: '#f8f9fa',
                    borderBottom: '1px solid rgba(0,0,0,.125)'
                }}
            >
                {image.thumbnail_url ? (
                    <img
                        src={image.thumbnail_url}
                        className="card-img-top"
                        alt={image.title}
                        height={image.thumbnail_height}
                        width={image.thumbnail_width}
                        style={{
                            maxHeight: '100%',
                            objectFit: 'contain'
                        }}
                    />
                ) : (
                    <div
                        style={{
                            textAlign: 'center',
                            color: '#6c757d',
                            display: 'flex',
                            flexDirection: 'column',
                            justifyContent: 'center',
                            alignItems: 'center',
                            fontSize: '0.9em'
                        }}
                    >
                        <svg
                            className="bi mb-1"
                            width="2em"
                            height="2em"
                            fill="currentColor"
                            viewBox="0 0 16 16"
                        >
                            <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0M5.028 11.02a.5.5 0 0 0-.04.28.99.99 0 0 0 .841.839c.295.054.584.04.84-.028l1.898-2.093a.25.25 0 0 1 .372 0l1.898 2.093c.256.068.545.082.84.028a.99.99 0 0 0 .84-.84.5.5 0 0 0-.04-.28l-1.898-2.092a.25.25 0 0 1 0-.372L10.972 6.98a.5.5 0 0 0 .04-.28.99.99 0 0 0-.841-.839c-.295-.054-.584-.04-.84.028L8.376 8.908a.25.25 0 0 1-.372 0L6.106 6.815c-.256-.068-.545-.082-.84-.028a.99.99 0 0 0-.84.84.5.5 0 0 0 .04.28l1.898 2.092a.25.25 0 0 1 0 .372z" />
                        </svg>
                        No Thumbnail
                        <br />
                        Available
                    </div>
                )}
            </div>
            <Card.Body className="d-flex flex-column">
                <h6 className="card-title">{image.title}</h6>
                {showViewButton && (
                    <Button
                        variant="primary"
                        size="sm"
                        className="mt-auto"
                        onClick={handleViewClick}
                    >
                        View
                    </Button>
                )}
            </Card.Body>
        </Card>
    );
};

export default ImageCard;
