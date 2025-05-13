import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Container, Breadcrumb, Spinner, Alert } from 'react-bootstrap';
import FolderWall from '../components/folder/FolderWall';
import ImageWall from '../components/image/ImageWall';
import type { ImageFolderSchema } from '../api';
import type { ImageThumbnailSchema } from '../api';
import { folderGetDetails, imageGetThumbInfo } from '../api';

export type BreadcrumbSchema = {
  id: number;
  name: string;
};

export type ImageFolderDetailSchema = {
  breadcrumbs: Array<BreadcrumbSchema>;
  child_folders: Array<ImageFolderSchema>;
  folder_images: Array<ImageThumbnailSchema>;
  has_children: boolean;
  id: number;
  image_count: number;
  name: string;
};

interface FolderDetailProps {}

const FolderDetail: React.FC<FolderDetailProps> = () => {
  const { id } = useParams<{ id: string }>();
  const folderId = parseInt(id || '0', 10);
  const navigate = useNavigate();

  const [folderDetail, setFolderDetail] = useState<ImageFolderDetailSchema | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFolderDetail = async () => {
      if (!folderId) return;

      try {
        setLoading(true);
        const response = await folderGetDetails({
          path: {
          folder_id: folderId
        }
        });
        setFolderDetail(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to load folder details. Please try again later.');
        console.error('Error fetching folder detail:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchFolderDetail();
  }, [folderId]);

  if (loading) {
    return (
      <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: '200px' }}>
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Loading...</span>
        </Spinner>
      </Container>
    );
  }

  if (error || !folderDetail) {
    return (
      <Container>
        <Alert variant="danger">{error || 'Folder not found'}</Alert>
      </Container>
    );
  }

  return (
    <Container fluid>
      {/* Breadcrumb navigation */}
      <Breadcrumb className="mt-3 mb-4">
        <Breadcrumb.Item linkAs={Link} linkProps={{ to: "/" }}>Home</Breadcrumb.Item>
        {folderDetail.breadcrumbs.map((crumb, index) => (
          <Breadcrumb.Item
            key={crumb.id}
            linkAs={Link}
            linkProps={{ to: `/folders/${crumb.id}` }}
            active={index === folderDetail.breadcrumbs.length - 1}
          >
            {crumb.name}
          </Breadcrumb.Item>
        ))}
      </Breadcrumb>

      <h1 className="mb-4">{folderDetail.name}</h1>

      {/* Child Folders Section */}
      {folderDetail.has_children && folderDetail.child_folders.length > 0 && (
        <>
          <h2 className="mb-3">Folders</h2>
          <FolderWall
            folders={folderDetail.child_folders}
            buttonText="Open"
            truncateDescription={100}
            onFolderClick={(childId) => {
              navigate(`/folders/${childId}`);
            }}
          />
          <hr className="my-5" />
        </>
      )}

      {/* Images Section */}
      {folderDetail.folder_images.length > 0 ? (
        <>
          <h2 className="mb-3">Images ({folderDetail.image_count})</h2>
          <ImageWall
            images={folderDetail.folder_images}
            onImageClick={async (imageId) => {
              try {
                // Get detailed thumbnail info when an image is clicked
                const thumbInfo = await imageGetThumbInfo({
                    path: {
                      image_id: imageId
                    }
                });

                // Handle the thumbnail info as needed
                console.log("Thumbnail info:", thumbInfo.data);

                // You could open a modal with the image or navigate to an image detail page
                // navigate(`/images/${imageId}`);
              } catch (err) {
                console.error("Error fetching thumbnail info:", err);
              }
            }}
            columns={4}
          />
        </>
      ) : (
        <Alert variant="info">This folder contains no images.</Alert>
      )}
    </Container>
  );
};

export default FolderDetail;
