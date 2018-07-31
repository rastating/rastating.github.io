---
layout: single
title: "C# XNA Per Pixel Collision Detection on Rotated Objects"
date: 2011-12-19 22:39:00 +0100
categories:
  - xna
  - programming
tags:
  - csharp
  - collision detection
  - rotation
  - transformation
---
I've been working on a new project this week which requires per pixel collision detection, however all the game objects that I need to detect the collisions on need to be rotated dynamically which introduced a lot of trouble when trying to detect collisions.

To save anyone else from having to jump through hoops trying to figure this out, I've put together a class called CollidableObject which will store a texture, position in world space and rotation factor and allow you to detect collisions between them by calling the IsColliding method.

In order for this class to work properly, you will also have to draw your textures using the rotation values (even if you aren't rotating your sprite) like so:

```csharp
// If the player is colliding with the enemy turn the screen red
if (this.player.IsColliding(this.enemy))
{
	GraphicsDevice.Clear(Color.Red);
}

// Draw the player to the screen
spriteBatch.Draw(this.player.Texture,
	this.player.Position,
	null,
	Color.White,
	this.player.Rotation,
	this.player.Origin,
	1.0f,
	SpriteEffects.None,
	0.0f);
```

It doesn't support the use of sprite sheets or animation, however you should be able to modify it easily to suit your needs.

See below the full class:

```csharp
// See https://rastating.github.io/xna-per-pixel-collision-detection-on-rotated-objects/ for details on how to use this class

using System;
using Microsoft.Xna;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;

namespace rastating
{
    /// <summary>
    /// An object that can be used to depict a sprite in world space which can detect pixel level collisions with other CollidableObjects
    /// </summary>
    public class CollidableObject
    {
        #region Fields

        private Texture2D texture;
        private Vector2 position;
        private float rotation;
        private Vector2 origin;
        private Color[] textureData;

        #endregion

        #region Properties

        /// <summary>
        /// The current position of the object in world space
        /// </summary>
        public Vector2 Position
        {
            get { return this.position; }
        }

        /// <summary>
        /// The currently loaded texture
        /// </summary>
        public Texture2D Texture
        {
            get { return this.texture; }
        }

        /// <summary>
        /// The pixel data of the loaded texture
        /// </summary>
        public Color[] TextureData
        {
            get { return this.textureData; }
        }

        /// <summary>
        /// The rotation factor
        /// </summary>
        public float Rotation
        {
            get
            {
                return this.rotation;
            }
            set
            {
                this.rotation = value;
            }
        }

        /// <summary>
        /// The origin of the object, by default this is the center point of the texture.
        /// </summary>
        public Vector2 Origin
        {
            get { return this.origin; }
            set { this.origin = value; }
        }

        /// <summary>
        /// A Rectangle that holds the width and height of the texture and zero in the X and Y points.
        /// </summary>
        public Rectangle Rect
        {
            get { return new Rectangle(0, 0, this.Texture.Width, this.Texture.Height); }
        }

        /// <summary>
        /// A Matrix based on the current rotation and position.
        /// </summary>
        public Matrix Transform
        {
            get
            {
                return Matrix.CreateTranslation(new Vector3(-this.Origin, 0.0f)) *
                                        Matrix.CreateRotationZ(this.Rotation) *
                                        Matrix.CreateTranslation(new Vector3(this.Position, 0.0f));
            }
        }

        /// <summary>
        /// An axis aligned rectangle which fully contains an arbitrarily transformed axis aligned rectangle.
        /// </summary>
        public Rectangle BoundingRectangle
        {
            get { return CalculateBoundingRectangle(this.Rect, this.Transform); }
        }

        #endregion

        #region Constructors

        /// <summary>
        /// Construct a new CollidableObject with a default texture and position in world space.
        /// </summary>
        /// <param name="texture">The texture associated with the object</param>
        /// <param name="position">The position of the object in world space</param>
        public CollidableObject(Texture2D texture, Vector2 position) : this(texture, position, 0.0f)
        {
        }

        /// <summary>
        /// Constructs a new CollidableObject with a default texture, position and rotation in world space.
        /// </summary>
        /// <param name="texture">The texture associated with the object</param>
        /// <param name="position">The position of the object in world space</param>
        /// <param name="rotation">The rotation factor</param>
        public CollidableObject(Texture2D texture, Vector2 position, float rotation)
        {
            this.LoadTexture(texture);
            this.position = position;
            this.rotation = rotation;
        }

        #endregion

        #region Instance Methods

        /// <summary>
        /// Moves the object left by the value passed in moveBy.
        /// </summary>
        /// <param name="moveBy">The floating point factor to move the object by</param>
        public void MoveLeft(float moveBy)
        {
            this.position.X -= moveBy;
        }

        /// <summary>
        /// Moves the object right by the value passed in moveBy.
        /// </summary>
        /// <param name="moveBy">The floating point factor to move the object by</param>
        public void MoveRight(float moveBy)
        {
            this.position.X += moveBy;
        }

        /// <summary>
        /// Moves the object up by the value passed in moveBy.
        /// </summary>
        /// <param name="moveBy">The floating point factor to move the object by</param>
        public void MoveUp(float moveBy)
        {
            this.position.Y -= moveBy;
        }

        /// <summary>
        /// Moves the object down by the value passed in moveBy.
        /// </summary>
        /// <param name="moveBy">The floating point factor to move the object by</param>
        public void MoveDown(float moveBy)
        {
            this.position.Y += moveBy;
        }

        /// <summary>
        /// Rotates the object by the value passed in moveBy, which can be both positive or negative to rotate in different directions.
        /// </summary>
        /// <param name="rotateBy">The floating point factor to move the object by</param>
        public void Rotate(float rotateBy)
        {
            if (rotateBy < 0)
            {
                this.rotation -= rotateBy;
            }
            else
            {
                this.rotation += rotateBy;
            }
        }

        /// <summary>
        /// Detects a pixel level collision between two CollidableObjects.
        /// </summary>
        /// <param name="collidable">The CollidableObject to check a collision against</param>
        /// <returns>True if colliding, false if not.</returns>
        public bool IsColliding(CollidableObject collidable)
        {
            bool retval = false;

            if (this.BoundingRectangle.Intersects(collidable.BoundingRectangle))
            {
                if (IntersectPixels(this.Transform, this.Texture.Width, this.Texture.Height, this.TextureData, collidable.Transform, collidable.Texture.Width, collidable.Texture.Height, collidable.TextureData))
                {
                    retval = true;
                }
            }

            return retval;
        }

        /// <summary>
        /// Loads a new texture and resets the origin to be the center point of the texture, the previous transformation values will be maintained.
        /// </summary>
        /// <param name="texture">The new texture to load</param>
        public void LoadTexture(Texture2D texture)
        {
            this.texture = texture;
            this.origin = new Vector2(texture.Width / 2, texture.Height / 2);
            this.textureData = new Color[texture.Width * texture.Height];
            this.texture.GetData(this.textureData);
        }

        /// <summary>
        /// Loads a new texture and origin, the previous transformation values will be maintained.
        /// </summary>
        /// <param name="texture">The new texture to load</param>
        /// <param name="origin">The new origin point</param>
        public void LoadTexture(Texture2D texture, Vector2 origin)
        {
            this.LoadTexture(texture);
            this.origin = origin;
        }

        #endregion

        #region Static Methods

        /// <summary>
        /// Determines if there is overlap of the non-transparent pixels
        /// between two sprites.
        /// </summary>
        /// <param name="rectangleA">Bounding rectangle of the first sprite</param>
        /// <param name="dataA">Pixel data of the first sprite</param>
        /// <param name="rectangleB">Bouding rectangle of the second sprite</param>
        /// <param name="dataB">Pixel data of the second sprite</param>
        /// <returns>True if non-transparent pixels overlap; false otherwise</returns>
        public static bool IntersectPixels(Rectangle rectangleA, Color[] dataA, Rectangle rectangleB, Color[] dataB)
        {
            // Find the bounds of the rectangle intersection
            int top = Math.Max(rectangleA.Top, rectangleB.Top);
            int bottom = Math.Min(rectangleA.Bottom, rectangleB.Bottom);
            int left = Math.Max(rectangleA.Left, rectangleB.Left);
            int right = Math.Min(rectangleA.Right, rectangleB.Right);

            // Check every point within the intersection bounds
            for (int y = top; y < bottom; y++)
            {
                for (int x = left; x < right; x++)
                {
                    // Get the color of both pixels at this point
                    Color colorA = dataA[(x - rectangleA.Left) +
                                         (y - rectangleA.Top) * rectangleA.Width];
                    Color colorB = dataB[(x - rectangleB.Left) +
                                         (y - rectangleB.Top) * rectangleB.Width];

                    // If both pixels are not completely transparent,
                    if (colorA.A != 0 && colorB.A != 0)
                    {
                        // then an intersection has been found
                        return true;
                    }
                }
            }

            // No intersection found
            return false;
        }

        /// <summary>
        /// Determines if there is overlap of the non-transparent pixels between two
        /// sprites.
        /// </summary>
        /// <param name="transformA">World transform of the first sprite.</param>
        /// <param name="widthA">Width of the first sprite's texture.</param>
        /// <param name="heightA">Height of the first sprite's texture.</param>
        /// <param name="dataA">Pixel color data of the first sprite.</param>
        /// <param name="transformB">World transform of the second sprite.</param>
        /// <param name="widthB">Width of the second sprite's texture.</param>
        /// <param name="heightB">Height of the second sprite's texture.</param>
        /// <param name="dataB">Pixel color data of the second sprite.</param>
        /// <returns>True if non-transparent pixels overlap; false otherwise</returns>
        public static bool IntersectPixels(Matrix transformA, int widthA, int heightA, Color[] dataA, Matrix transformB, int widthB, int heightB, Color[] dataB)
        {
            // Calculate a matrix which transforms from A's local space into
            // world space and then into B's local space
            Matrix transformAToB = transformA * Matrix.Invert(transformB);

            // When a point moves in A's local space, it moves in B's local space with a
            // fixed direction and distance proportional to the movement in A.
            // This algorithm steps through A one pixel at a time along A's X and Y axes
            // Calculate the analogous steps in B:
            Vector2 stepX = Vector2.TransformNormal(Vector2.UnitX, transformAToB);
            Vector2 stepY = Vector2.TransformNormal(Vector2.UnitY, transformAToB);

            // Calculate the top left corner of A in B's local space
            // This variable will be reused to keep track of the start of each row
            Vector2 yPosInB = Vector2.Transform(Vector2.Zero, transformAToB);

            // For each row of pixels in A
            for (int yA = 0; yA < heightA; yA++)
            {
                // Start at the beginning of the row
                Vector2 posInB = yPosInB;

                // For each pixel in this row
                for (int xA = 0; xA < widthA; xA++)
                {
                    // Round to the nearest pixel
                    int xB = (int)Math.Round(posInB.X);
                    int yB = (int)Math.Round(posInB.Y);

                    // If the pixel lies within the bounds of B
                    if (0 <= xB && xB < widthB &&
                        0 <= yB && yB < heightB)
                    {
                        // Get the colors of the overlapping pixels
                        Color colorA = dataA[xA + yA * widthA];
                        Color colorB = dataB[xB + yB * widthB];

                        // If both pixels are not completely transparent,
                        if (colorA.A != 0 && colorB.A != 0)
                        {
                            // then an intersection has been found
                            return true;
                        }
                    }

                    // Move to the next pixel in the row
                    posInB += stepX;
                }

                // Move to the next row
                yPosInB += stepY;
            }

            // No intersection found
            return false;
        }

        /// <summary>
        /// Calculates an axis aligned rectangle which fully contains an arbitrarily
        /// transformed axis aligned rectangle.
        /// </summary>
        /// <param name="rectangle">Original bounding rectangle.</param>
        /// <param name="transform">World transform of the rectangle.</param>
        /// <returns>A new rectangle which contains the trasnformed rectangle.</returns>
        public static Rectangle CalculateBoundingRectangle(Rectangle rectangle, Matrix transform)
        {
            // Get all four corners in local space
            Vector2 leftTop = new Vector2(rectangle.Left, rectangle.Top);
            Vector2 rightTop = new Vector2(rectangle.Right, rectangle.Top);
            Vector2 leftBottom = new Vector2(rectangle.Left, rectangle.Bottom);
            Vector2 rightBottom = new Vector2(rectangle.Right, rectangle.Bottom);

            // Transform all four corners into work space
            Vector2.Transform(ref leftTop, ref transform, out leftTop);
            Vector2.Transform(ref rightTop, ref transform, out rightTop);
            Vector2.Transform(ref leftBottom, ref transform, out leftBottom);
            Vector2.Transform(ref rightBottom, ref transform, out rightBottom);

            // Find the minimum and maximum extents of the rectangle in world space
            Vector2 min = Vector2.Min(Vector2.Min(leftTop, rightTop),
                                      Vector2.Min(leftBottom, rightBottom));
            Vector2 max = Vector2.Max(Vector2.Max(leftTop, rightTop),
                                      Vector2.Max(leftBottom, rightBottom));

            // Return that as a rectangle
            return new Rectangle((int)min.X, (int)min.Y,
                                 (int)(max.X - min.X), (int)(max.Y - min.Y));
        }

        #endregion
    }
}
```
