import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Container, Breadcrumb, Spinner, Alert } from 'react-bootstrap';
import FolderWall from '../components/folder/FolderWall';
import ImageWall from '../components/image/ImageWall';
import { folderGetDetails, imageGetThumbInfo } from '../api';
import type { FolderDetailSchema, ImageThumbnailSchema } from '../api';


interface FolderDetailProps {}

const FolderDetail: React.FC<FolderDetailProps> = () => {
  const { id } = useParams<{ id: string }>();
  const folderId = parseInt(id || '0', 10);
  const navigate = useNavigate();

  const [folderDetail, setFolderDetail] = useState<FolderDetailSchema | null>(null);
  const [imageThumbs, setImageThumbs] = useState<ImageThumbnailSchema[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [loadingImages, setLoadingImages] = useState<boolean>(false);
  const [imageError, setImageError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFolderDetail = async () => {
      if (!folderId) {
        setLoading(false);
        setError('Invalid folder ID.');
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const response = await folderGetDetails({
          path: {
          folder_id: folderId
        }
        });
        setFolderDetail(response.data === undefined ? null : response.data);
      } catch (err) {
        setError('Failed to load folder details. Please try again later.');
        console.error('Error fetching folder detail:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchFolderDetail();
  }, [folderId]);

  useEffect(() => {
    const fetchImageThumbnails = async () => {
      if (!folderDetail || !folderDetail.folder_images || folderDetail.folder_images.length === 0) {
        setImageThumbs([]);
        setLoadingImages(false); // Ensure loading is false if there are no images listed
        setImageError(null);
        return;
      }

      setLoadingImages(true);
      setImageError(null);

      try {
        const thumbInfoPromises = folderDetail.folder_images.map(imageId =>
          imageGetThumbInfo({ path: { image_id: imageId } })
            .then(response => response.data)
            .catch(err => {
              console.error(`Error fetching thumbnail info for image ID ${imageId}:`, err);
              return null;
            })
        );

        const results = await Promise.all(thumbInfoPromises);
        const successfulThumbs = results.filter(item => item !== null) as ImageThumbnailSchema[];

        setImageThumbs(successfulThumbs);

        if (successfulThumbs.length !== folderDetail.folder_images.length) {
            setImageError(`Failed to load thumbnail info for ${folderDetail.folder_images.length - successfulThumbs.length} out of ${folderDetail.folder_images.length} images.`);
        }

      } catch (err) {
        console.error('Overall error fetching image thumbnails:', err);
        setImageError('Failed to load image thumbnails.');
        setImageThumbs([]);
      } finally {
        setLoadingImages(false);
      }
    };

    fetchImageThumbnails();
  }, [folderDetail]);


  if (loading) {
     return (
       <Container className="d-flex justify-content-center align-items-center" style={{ minHeight: '200px' }}>
         <Spinner animation="border" role="status">
           <span className="visually-hidden">Loading folder details...</span>
         </Spinner>
       </Container>
     );
   }

  if (error || !folderDetail) {
     return (
       <Container className="mt-4">
         <Alert variant="danger">{error || 'Folder not found or an unexpected error occurred.'}</Alert>
       </Container>
     );
   }

  return (
     <Container fluid>
       {/* Breadcrumb navigation */}
       <Breadcrumb className="mt-3 mb-4">
         <Breadcrumb.Item linkAs={Link} linkProps={{ to: "/folders" }}>Home</Breadcrumb.Item>
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

       <h1 className="mb-4">Current Folder: {folderDetail.name}</h1>

       {/* Child Folders Section - Heading always visible */}
       <>
         <h2 className="mb-3">Child Folders</h2>
         {/* Render FolderWall if there are child folders, otherwise show a message */}
         {folderDetail.child_folders.length > 0 ? (
           <FolderWall
             folders={folderDetail.child_folders}
             buttonText="Open"
             truncateDescription={100}
             onFolderClick={(childId) => {
               navigate(`/folders/${childId}`);
             }}
           />
         ) : (
           <Alert variant="info">This folder contains no child folders.</Alert>
         )}
       </> {/* End Folders Section Fragment */}

       {/* Separator Line - Always visible when folder details are loaded */}
       <hr className="my-5" />

       {/* Images Section - Heading always visible */}
       <>
         <h2 className="mb-3">Images ({folderDetail.folder_images.length})</h2>
         {/* Render image content based on loading, errors, and data */}
         {loadingImages ? (
           <div className="d-flex justify-content-center align-items-center my-3">
             <Spinner animation="border" size="sm" role="status">
               <span className="visually-hidden">Loading images...</span>
             </Spinner>
             <span className="ms-2">Loading images...</span>
           </div>
         ) : imageError ? ( // Show image error if present after loading
           <Alert variant="warning">{imageError}</Alert>
         ) : imageThumbs.length > 0 ? ( // Show ImageWall if images loaded successfully
           <ImageWall
             images={imageThumbs} // Pass the fetched image thumbnail data
             onImageClick={(imageId) => {
                 navigate(`/images/${imageId}`);
             }}
             columns={4}
           />
         ) : ( // Show message if no images loaded successfully (covers folder_images.length === 0 initially or failed fetch)
           <Alert variant="info">This folder contains no images.</Alert>
         )}
       </> {/* End Images Section Fragment */}

     </Container>
  );
};

export default FolderDetail;
